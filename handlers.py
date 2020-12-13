from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater
)
from config import TOKEN
import logging, re
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import engine, User, Business, Category

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
FETCH_PREFERENCES, CLASS_STATE, STORE_INFO, SME_DETAILS, CHOOSING, CUSTOMER_DETAILS, ADD_PRODUCTS = range(7)

reply_keyboard = [
    ['SME', 'Customer']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


# Define callback handler
def start(update, context: CallbackContext) -> int:
    print("You called")
    update.message.reply_text(
        "Hi fellow, Welcome to SMEbot ,"
        "Please tell me about yourself, "
        "provide your full name, email, and phone number, "
        "separated by comma each e.g: "
        "John Doe, JohnD@gmail.com, +234567897809"
    )
    return CLASS_STATE


def classer(update, context):
    data = update.message.text.split(',')
    new_user = User(
        name=data[0], email=data[1],
        telephone=data[2]
    )
    session.add(new_user)
    try:
        session.commit()
    except IntegrityError:
        print("Error: Duplicate data")
        session.rollback()
        return CLASS_STATE
    update.message.reply_text(
        text="Collected information succesfully!.."
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    return CHOOSING


def customer_details(update, context: CallbackContext) -> int:
    categories = [
        ['Clothing/Fashion', 'Hardware Accessories'],
        ['Food/Kitchen Ware', 'ArtnDesign']
    ]
    markup = ReplyKeyboardMarkup(categories, one_time_keyboard=True)
    update.message.reply_text(
        "Here's a list of categories available"
        "Choose one that matches your interest",
        reply_markup=markup
    )

    return FETCH_PREFERENCES


def fetch_preference(update, context: CallbackContext) -> int:
    if update.message.text:
        choice = update.message.text
        result = session.query(Category).filter_by(name=choice).first().sme
        print(result)
        for i in result:
            button = [[InlineKeyboardButton(
                text='View Products',
                callback_data=i.name
            )]]
            update.message.reply_text(
                f"{i.name}",
                reply_markup=InlineKeyboardMarkup(button)
            )
    return FETCH_PREFERENCES


def fetch_bizpref(update, context):
    choice = update.message.text
    biz = session.query(Business).filter_by(name=choice).first().product
    print(biz)
    for i in biz:
        update.message.reply_text(
            f"{i.name}"
        )
    return


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
                    customer_details
                )
            ],
            FETCH_PREFERENCES: [
                MessageHandler(
                    Filters.regex(r'^(Clothing/Fashion|Hardware Accessories|Food/Kitchen Ware|ArtnDesign)$'),
                    fetch_preference
                ),
                MessageHandler(
                    Filters.all, fetch_bizpref
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
