import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

import config
from classifier import process_place

logger = logging.getLogger(__name__)

#TODO: Remove comment from 2nd ID
ALLOWED_USERS = {config.TELEGRAM_USER_ID_1}#, config.TELEGRAM_USER_ID_2}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        return

    text = update.message.text.strip()
    if not text:
        return

    try:
        reply = process_place(text, update.message.date)
    except Exception as e:
        logger.exception("Error processing place")
        error_type = type(e).__name__
        reply = f"Something went wrong ({error_type}). Please try again."

    await update.message.reply_text(reply)


def create_app():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
