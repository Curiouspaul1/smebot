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
import logging, re
from sqlalchemy.orm import sessionmaker
from models import engine, Customer, SmeOwner, Business

Session = sessionmaker(bind=engine)
session = Session()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define Options
CLASS_STATE, SME_DETAILS, CHOOSING, CUSTOMER_DETAILS, ADD_PRODUCTS = range(5)

reply_keyboard = [
    ['SME', 'Customer']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


# Define callback handler
def start(update, context: CallbackContext) -> int:
    print("You called")
    update.message.reply_text(
        text="Hi fellow, Welcome to SMEbot ,"
        "Please tell me about yourself, "
        "provide your full name, email, and phone number, "
        "separated by comma each e.g: "
        "John Doe, JohnD@gmail.com, +234567897809"
    )

    return CLASS_STATE


def classer(update, context):
    user = update.message.from_user
    update.message.reply_text(
        f"Welcome {user}, "
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    return CHOOSING


def cpdetails(update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Awesome!, please tell me about yourself, "
        "provide your full name, email, and phone number, "
        "separated by comma each e.g: "
        "John Doe, JohnD@gmail.com, +234567897809",
        reply_markup=ReplyKeyboardRemove()
    )

    return CHOOSING


def smedetails(update, context: CallbackContext) -> int:
    user = update.message.from_user
    msg = update.message.text.split(',')
    print(msg)
    update.message.reply_text(
        f"Great! {user.first_name}, please tell me about your business, "
        "provide your BrandName, Brand email, and phone number, Niche "
        "separated by comma each e.g: "
        "JDWears, JDWears@gmail.com, +234567897809, "
        "Fashion/Clothing", reply_markup=ReplyKeyboardRemove()
    )

    return ADD_PRODUCTS

#def customer_details(updata, context: CallbackContext) -> int:


def products(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Thanks for filling the form",
        reply_markup=ReplyKeyboardRemove()
    )
    return "Done"


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


#def pick_interest()


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CLASS_STATE: [
                MessageHandler(
                    Filters.all, classer
                )
            ],
            CHOOSING: [
                MessageHandler(
                    Filters.regex(r'^(SME|sme|Sme)$'), smedetails
                ),
                MessageHandler(
                    Filters.regex(r'(^Customer|customer|CUSTOMER)$'),
                    cpdetails
                )
            ],
            ADD_PRODUCTS: [
                MessageHandler(
                    Filters.all,
                    products
                )
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
