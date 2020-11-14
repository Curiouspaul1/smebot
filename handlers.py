from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update
)
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater
)
from config import TOKEN
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define Options
PERSONAL_DETAILS, SME_DETAILS, ADD_PRODUCTS = range(3)


# Define callback handler
def start(update):
    print("You called")
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


def pdetails(update, context: CallbackContext):
    update.message.reply_text(
        "Awesome!, please tell me about yourself, "
        "provide your full name, email, and phone number, "
        "separated by comma each e.g: "
        "John Doe, JohnD@gmail.com, +234567897809",
        reply_markup=ReplyKeyboardRemove()
    )

    return SME_DETAILS


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PERSONAL_DETAILS: [
                MessageHandler(Filters.regex('(W,)+'), pdetails)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    print("HELLO SOLARSYS")
    dispatcher.add_handler(start_handler)
    #dispatcher.add_handler(conv_handler)
    # Start the Bot
