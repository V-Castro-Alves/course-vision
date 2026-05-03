import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.handlers import set_language, setlang_callback


@pytest.fixture(autouse=True)
def mock_i18n():
    with patch("core.handlers.t") as mock_t:
        mock_t.side_effect = lambda key, *args, **kwargs: key
        yield mock_t


@pytest.mark.asyncio
async def test_set_language_sends_keyboard():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await set_language.__wrapped__(update, context)

    update.message.reply_text.assert_called_once()
    args, kwargs = update.message.reply_text.call_args
    assert args[0] == "setlang_prompt"
    assert "reply_markup" in kwargs
    # Verify keyboard buttons
    keyboard = kwargs["reply_markup"].inline_keyboard
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "Português 🇧🇷"
    assert keyboard[0][0].callback_data == "setlang:pt-br"
    assert keyboard[0][1].text == "English 🇺🇸"
    assert keyboard[0][1].callback_data == "setlang:en"


@pytest.mark.asyncio
async def test_setlang_callback_success():
    update = MagicMock()
    query = MagicMock()
    query.data = "setlang:pt-br"
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    context = MagicMock()
    context.user_data = {}

    with (
        patch("core.handlers.db_connect") as mock_db,
        patch("core.handlers.closing") as mock_closing,
        patch("core.handlers.auth_user", return_value=True),
    ):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_closing.return_value.__enter__.return_value = mock_conn

        await setlang_callback(update, context)

        query.answer.assert_called_once()
        mock_conn.cursor().execute.assert_called_once_with(
            "UPDATE users SET lang = ? WHERE telegram_id = ?", ("pt-br", 123)
        )
        mock_conn.commit.assert_called_once()
        query.edit_message_text.assert_called_once()
        assert query.edit_message_text.call_args[0][0] == "setlang_success"
        assert context.user_data["lang"] == "pt-br"
