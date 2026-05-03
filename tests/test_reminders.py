import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.handlers import set_reminder


@pytest.fixture(autouse=True)
def mock_i18n():
    with patch("core.handlers.t") as mock_t:
        mock_t.side_effect = lambda key, *args, **kwargs: key
        yield mock_t


@pytest.mark.asyncio
async def test_set_reminder_no_args():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []

    await set_reminder.__wrapped__(
        update, context
    )  # Use __wrapped__ to skip check_auth for unit test

    update.message.reply_text.assert_called_once()
    assert "remind_usage" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_set_reminder_off():
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["off"]

    with patch("core.handlers.db_connect") as mock_db, patch(
        "core.handlers.closing"
    ) as mock_closing:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_closing.return_value.__enter__.return_value = mock_conn

        await set_reminder.__wrapped__(update, context)

        mock_conn.cursor().execute.assert_any_call(
            "UPDATE users SET reminder_minutes = NULL WHERE telegram_id = ?", (123,)
        )
        mock_conn.commit.assert_called_once()
        update.message.reply_text.assert_called_once_with("remind_off")


@pytest.mark.asyncio
async def test_set_reminder_success():
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["15"]

    with patch("core.handlers.db_connect") as mock_db, patch(
        "core.handlers.closing"
    ) as mock_closing:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_closing.return_value.__enter__.return_value = mock_conn

        await set_reminder.__wrapped__(update, context)

        mock_conn.cursor().execute.assert_any_call(
            "UPDATE users SET reminder_minutes = ? WHERE telegram_id = ?", (15, 123)
        )
        mock_conn.commit.assert_called_once()
        update.message.reply_text.assert_called_once_with("remind_success")
