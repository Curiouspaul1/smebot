from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater, CallbackQueryHandler
)
from config import TOKEN, api_key, api_secret
import logging, re
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import engine, User, Business, Category
import cloudinary


Session = sessionmaker(bind=engine)
session = Session()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


# configure cloudinary
cloudinary.config(
    cloud_name="curiouspaul",
    api_key=api_key,
    api_secret=api_secret
)

# Define Options
FETCH_PREFERENCES, CHOOSESME_CAT, FETCH_SUBPREFERENCE, CLASS_STATE, SME_DETAILS, CHOOSING, ADD_PRODUCTS = range(7)

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
    print(update.message.from_user)
    name = update.message.from_user.first_name + ' ' + \
        update.message.from_user.last_name
    print(name)
    data = update.message.text.split(',')
    new_user = User(
        name=name, email=data[1],
        telephone=data[2]
    )
    session.add(new_user)
    try:
        session.commit()
    except IntegrityError:
        update.message.reply_text(
            "User with email already exists, try again"
        )
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
    return FETCH_SUBPREFERENCE


def fetch_bizpref(update, context):
    print(update)
    choice = update.callback_query.data
    print(choice)
    biz = session.query(Business).filter_by(name=choice).first().product
    for i in biz:
        update.callback_query.message.reply_text(
            f"{i.name}: \n"
            f"Description: \n {i.description}"
        )
    # TODO: Add contact button
    return


def smedetails(update, context: CallbackContext) -> int:
    global owner
    user = update.message.from_user
    msg = update.message.text.split(',')
    # find user in db
    name = update.message.from_user.first_name + ' ' + \
        update.message.from_user.last_name
    owner = session.query(User).filter_by(name=name).first()
    owner.is_smeowner = True
    session.commit()
    print(msg)
    update.message.reply_text(
        f"Great! {user.first_name}, please tell me about your business, "
        "provide your BrandName, Brand email, Address, and phone number"
        "in that order, each separated by comma(,) each e.g: "
        "JDWears, JDWears@gmail.com, 101-Mike Avenue-Ikeja, +234567897809",
        reply_markup=ReplyKeyboardRemove()
    )

    return CHOOSESME_CAT


def smecat(update, context):
    # create business
    data = update.message.text.split(',')
    newbiz = Business(
        name=data[0], email=data[1],
        address=data[2], telephone=data[3],
        owner=owner
    )
    session.add(newbiz)
    try:
        session.commit()
    except IntegrityError:
        print("Duplicate data")
        update.mesage.reply_text(
            "Business with email already exists, try again"
        )
        return CHOOSESME_CAT
    categories = [
        ['Clothing/Fashion', 'Hardware Accessories'],
        ['Food/Kitchen Ware', 'ArtnDesign']
    ]
    markup = ReplyKeyboardMarkup(categories, one_time_keyboard=True)
    update.message.reply_text(
        "Pick a category for your business from the options",
        reply_markup=markup
    )
    return ADD_PRODUCTS


def products(update: Update, context: CallbackContext):
    # update business category
    biz = owner.sme
    cat_ = session.query(Category).filter_by(name=update.message.text).first()
    biz.category = cat_
    session.commit()
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
                )
            ],
            ADD_PRODUCTS: [
                MessageHandler(
                    Filters.all,
                    products
                )
            ],
            FETCH_SUBPREFERENCE: [
                CallbackQueryHandler(
                    fetch_bizpref
                )
            ],
            CHOOSESME_CAT: [
                MessageHandler(
                    Filters.all,
                    smecat
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
