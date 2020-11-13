from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update
)
from telegram.ext import Updater, CommandHandler
import os
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define Options
PERSONAL_DETAILS, SME_DETAILS, ADD_PRODUCTS = range(3)


# Define callback handler
def start(update):
    reply_keyboard = [
        ['SME', 'Consumer']
    ]

    update.message.reply_text(
        text="Hi fellow, Welcome to SMEbot \
            which of the follwing do you identify as? \
        ",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True
        )
    )

    return PERSONAL_DETAILS
