import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat, PhotoSize, Document, File
from telegram.ext import ContextTypes

from core.handlers import photo_upload, confirm_schedule_processing, upload_command
from core.database import init_db
from core.i18n import load_responses, t
import sqlite3
from datetime import datetime, timedelta


# Initialize i18n and DB for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    load_responses()
    # Use an in-memory database for testing
    with patch("core.database.DATABASE_PATH", ":memory:"):
        init_db()
        yield
        # Clean up if necessary, though in-memory DBs don't need explicit cleanup


@pytest.fixture(autouse=True)
def mock_authorized_user_id(monkeypatch):
    monkeypatch.setattr("core.database.AUTHORIZED_USER_ID", 123)


@pytest.fixture
def mock_context():
    application_mock = MagicMock()
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}  # Directly set user_data as a dictionary
    context.application = application_mock
    context.bot = AsyncMock()  # Ensure context.bot is an AsyncMock
    return context


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User, id=123, language_code="en")
    update.effective_chat = MagicMock(spec=Chat, id=123)
    update.message = MagicMock(spec=Message)
    update.message.photo = None
    update.message.document = None
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_file():
    file = MagicMock(spec=File)
    file.file_path = "https://example.com/test_photo.jpg"
    file.download_to_drive = AsyncMock()
    return file


@pytest.fixture
def mock_db_connection():
    # Use a real in-memory SQLite for more realistic testing of DB operations
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE NOT NULL, lang TEXT DEFAULT 'en')
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mime_type TEXT, image_blob BLOB, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, day_index INTEGER NOT NULL, class_date TEXT NOT NULL, subject TEXT NOT NULL, room TEXT NOT NULL, professor TEXT NOT NULL, code TEXT NOT NULL, raw TEXT NOT NULL, source_image_id INTEGER, FOREIGN KEY(source_image_id) REFERENCES raw_images(id))
    """
    )
    cursor.execute(
        """
        INSERT INTO users (telegram_id, lang) VALUES (?, ?)
    """,
        (123, "en"),
    )
    conn.commit()
    yield conn
    conn.close()


class NoCloseConnection:
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        if name == "close":
            return lambda: None
        return getattr(self._conn, name)


@pytest.fixture(autouse=True)
def mock_db_connect(mock_db_connection):
    wrapper = NoCloseConnection(mock_db_connection)
    with patch("core.database.db_connect", return_value=wrapper):
        with patch("core.handlers.db_connect", return_value=wrapper):
            yield


@pytest.mark.asyncio
async def test_photo_upload_sends_confirmation(mock_update, mock_context, mock_file):
    # Simulate sending a photo
    mock_update.message.photo = [
        MagicMock(spec=PhotoSize, file_id="test_file_id", width=100, height=100)
    ]
    mock_context.bot.get_file.return_value = mock_file

    await photo_upload(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert (
        t("photo_received_ask_process", update=mock_update, context=mock_context)
        in args[0]
    )
    assert "reply_markup" in kwargs
    assert mock_context.user_data["last_photo_file_id"] == "test_file_id"
    assert (
        mock_context.user_data["last_photo_message_id"]
        == mock_update.message.message_id
    )


@pytest.mark.asyncio
@patch("core.handlers.generate_with_model_fallback")
@patch("core.handlers.assign_dates_to_classes")
@patch(
    "core.handlers.normalize_row", side_effect=lambda x: x
)  # Mock normalize_row to return input
@patch(
    "core.handlers.should_skip_row", return_value=False
)  # Mock should_skip_row to not skip
async def test_confirm_schedule_processing_yes(
    mock_should_skip_row,
    mock_normalize_row,
    mock_assign_dates_to_classes,
    mock_generate_with_model_fallback,
    mock_update,
    mock_context,
    mock_file,
    mock_db_connection,  # Use the fixture
):
    # Setup for photo_upload first
    mock_update.effective_user.id = 123
    mock_update.message.photo = [
        MagicMock(spec=PhotoSize, file_id="test_file_id", width=100, height=100)
    ]
    mock_context.bot.get_file.return_value = mock_file
    await photo_upload(mock_update, mock_context)
    mock_update.message.reply_text.reset_mock()  # Clear calls from photo_upload

    # Simulate callback query for 'yes'
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.data = "process_schedule:yes"
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.effective_user.id = 123  # Ensure user ID is set for callback

    # Mock Gemini response
    mock_gemini_response = MagicMock()
    mock_gemini_response.parsed.rows = [
        MagicMock(
            class_code="MATH101",
            class_name="Calculus I",
            professor="Dr. Smith",
            classroom="Room 101",
        ),
        MagicMock(
            class_code="PHYS202",
            class_name="Physics II",
            professor="Dr. Jones",
            classroom="Lab 202",
        ),
    ]
    mock_generate_with_model_fallback.return_value = (
        mock_gemini_response,
        "gemini-flash",
    )

    # Mock assign_dates_to_classes
    mock_assign_dates_to_classes.return_value = [
        MagicMock(
            day_index=0,
            class_date=(datetime.now().date() + timedelta(days=0)).isoformat(),
            class_code="MATH101",
            class_name="Calculus I",
            professor="Dr. Smith",
            classroom="Room 101",
        ),
        MagicMock(
            day_index=1,
            class_date=(datetime.now().date() + timedelta(days=1)).isoformat(),
            class_code="PHYS202",
            class_name="Physics II",
            professor="Dr. Jones",
            classroom="Lab 202",
        ),
    ]

    # Execute confirmation handler
    await confirm_schedule_processing(mock_update, mock_context)

    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.edit_message_text.assert_called_once_with(
        t("processing_confirmed", update=mock_update, context=mock_context)
    )

    # Verify calls within _process_and_save_schedule
    mock_context.bot.send_message.assert_any_call(
        chat_id=mock_update.effective_chat.id,
        text=t(
            "image_received",
            user_id=mock_update.effective_user.id,
            context=mock_context,
        ),
    )
    mock_context.bot.send_message.assert_any_call(
        chat_id=mock_update.effective_chat.id,
        text=t(
            "extracting_schedule",
            user_id=mock_update.effective_user.id,
            context=mock_context,
        ),
    )
    mock_generate_with_model_fallback.assert_called_once()
    mock_context.bot.send_message.assert_any_call(
        chat_id=mock_update.effective_chat.id,
        text=t(
            "parsed_rows",
            user_id=mock_update.effective_user.id,
            context=mock_context,
            count=2,
        ),
    )
    mock_context.bot.send_message.assert_any_call(
        chat_id=mock_update.effective_chat.id,
        text=t(
            "parsing_success",
            user_id=mock_update.effective_user.id,
            context=mock_context,
            count=2,
            model="gemini-flash",
        ),
    )

    # Verify database interactions
    cursor = mock_db_connection.cursor()
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()
    assert len(classes) == 2
    assert classes[0]["code"] == "MATH101"
    assert classes[1]["subject"] == "Physics II"


@pytest.mark.asyncio
async def test_confirm_schedule_processing_no(mock_update, mock_context):
    # Setup for photo_upload first (to populate user_data)
    mock_update.message.photo = [
        MagicMock(spec=PhotoSize, file_id="test_file_id", width=100, height=100)
    ]
    mock_context.bot.get_file.return_value = MagicMock(
        spec=File, file_path="url", download_to_drive=AsyncMock()
    )
    await photo_upload(mock_update, mock_context)
    mock_update.message.reply_text.reset_mock()

    # Simulate callback query for 'no'
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.data = "process_schedule:no"
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.effective_user.id = 123

    with patch(
        "core.handlers._process_and_save_schedule"
    ) as mock_process_and_save_schedule:
        await confirm_schedule_processing(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once_with(
            t("processing_cancelled", update=mock_update, context=mock_context)
        )
        mock_process_and_save_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_photo_upload_unauthorized_user(mock_update, mock_context):
    mock_update.effective_user.id = 999  # Unauthorized ID
    mock_update.message.photo = [
        MagicMock(spec=PhotoSize, file_id="test_file_id", width=100, height=100)
    ]
    mock_context.bot.get_file.return_value = MagicMock(
        spec=File, file_path="url", download_to_drive=AsyncMock()
    )

    # This should be caught by the @check_owner decorator, so photo_upload itself won't run.
    # The decorator handles the reply.
    # To test the decorator, we need to apply the decorator in test or call it directly.
    # For now, let's assume the decorator works and test the handler's logic.
    # However, the decorator is *above* the handler. So it will block.

    # The @check_owner decorator is applied, it will prevent photo_upload from running
    # if the user is not authorized. The decorator itself sends the 'auth_denied' message.
    # So, we should check for that message.
    await photo_upload(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with(
        t("auth_denied", update=mock_update, context=mock_context)
    )


@pytest.mark.asyncio
async def test_upload_command_authorized_user(mock_update, mock_context):
    mock_update.effective_user.id = 123  # Directly set for authorized user test

    await upload_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once_with(
        t("upload_prompt", update=mock_update, context=mock_context)
    )


@pytest.mark.asyncio
async def test_upload_command_unauthorized_user(mock_update, mock_context):
    mock_update.effective_user.id = 999  # Unauthorized ID

    await upload_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once_with(
        t("auth_denied", update=mock_update, context=mock_context)
    )


# Test for handling document images
@pytest.mark.asyncio
async def test_photo_upload_document_image(mock_update, mock_context, mock_file):
    mock_document = MagicMock(
        spec=Document,
        file_id="doc_file_id",
        mime_type="image/png",
        file_name="schedule.png",
    )
    mock_update.message.document = mock_document
    mock_context.bot.get_file.return_value = mock_file

    await photo_upload(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert (
        t("photo_received_ask_process", update=mock_update, context=mock_context)
        in args[0]
    )
    assert "reply_markup" in kwargs
    assert mock_context.user_data["last_photo_file_id"] == "doc_file_id"
    assert (
        mock_context.user_data["last_photo_message_id"]
        == mock_update.message.message_id
    )
