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
from models import engine, User, Business, Category, Product
import cloudinary
from cloudinary.uploader import upload

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
FETCH_PREFERENCES, CHOOSESME_CAT, FETCH_SUBPREFERENCE, \
    CLASS_STATE, SME_DETAILS, \
    CHOOSING, ADD_PRODUCTS, FETCH_SMECONTACT = range(8)

reply_keyboard = [
    [
        InlineKeyboardButton(
            text="SME",
            callback_data="SME"
        ),
        InlineKeyboardButton(
            text="Customer",
            callback_data="Customer"
        )
    ]
]
markup = InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


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
    global customer
    customer = new_user
    update.message.reply_text(
        text="Collected information succesfully!.."
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    return CHOOSING


def customer_details(update, context: CallbackContext) -> int:
    if update.callback_query.data.lower() == 'sme':
        global owner
        user = update.callback_query.message.from_user
        # find user in db
        name = update.callback_query.message.chat.first_name + ' ' + \
            update.callback_query.message.chat.last_name
        owner = session.query(User).filter_by(name=name).first()
        owner.is_smeowner = True
        session.commit()
        update.callback_query.message.reply_text(
            f"Great! {user.first_name}, please tell me about your business, "
            "provide your BrandName, Brand email, Address, and phone number"
            "in that order, each separated by comma(,) each e.g: "
            "JDWears, JDWears@gmail.com, 101-Mike Avenue-Ikeja, +234567897809",
            reply_markup=ReplyKeyboardRemove()
        )

        return CHOOSESME_CAT
    categories = [
        [
            InlineKeyboardButton(
                text="Clothing/Fashion",
                callback_data="Clothing/Fashion"
            ),
            InlineKeyboardButton(
                text="Hardware Accessories",
                callback_data="Hardware Accessories"
            )
        ],
        [
            InlineKeyboardButton(
                text="Food/Kitchen Ware",
                callback_data="Food/Kitchen Ware"
            ),
            InlineKeyboardButton(
                text="ArtnDesign",
                callback_data="ArtnDesign"
            )
        ]
    ]
    # categories = [
    #     ['Clothing/Fashion', 'Hardware Accessories'],
    #     ['Food/Kitchen Ware', 'ArtnDesign']
    # ]
    # markup = ReplyKeyboardMarkup(categories, one_time_keyboard=True)
    update.callback_query.message.reply_text(
        "Here's a list of categories available"
        "Choose one that matches your interest",
        reply_markup=InlineKeyboardMarkup(categories)
    )

    return FETCH_PREFERENCES


def fetch_preference(update, context: CallbackContext) -> int:
    if update.callback_query.data:
        choice = update.callback_query.data
        result = session.query(Category).filter_by(name=choice).first().sme
        print(result)
        for i in result:
            button = [
                [
                    InlineKeyboardButton(
                        text='View Products',
                        callback_data=i.name
                    ),
                    InlineKeyboardButton(
                        text="Select for updates",
                        callback_data='pref'+','+i.name
                    )
                ]
            ]
            update.callback_query.message.reply_text(
                f"{i.name}".upper(),
                reply_markup=InlineKeyboardMarkup(button)
            )
    return FETCH_SUBPREFERENCE


def fetch_bizpref(update, context):
    if 'pref' in update.callback_query.data:
        choice = update.callback_query.data.split(',')
        customer.preference += choice[1] + ', '
        biz = session.query(Business).filter_by(name=choice[1]).first()
        session.commit()
        button = [
            [
                InlineKeyboardButton(
                    text="View more Businesses in same category",
                    callback_data=biz.category.name
                )
            ]
        ]
        update.callback_query.message.reply_text(
            "Preference set successfully",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return FETCH_PREFERENCES
    else:
        choice = update.callback_query.data
        biz = session.query(Business).filter_by(name=choice).first().product
        for i in biz:
            update.callback_query.message.reply_photo(
                photo=cloudinary.CloudinaryImage(i.image).build_url(
                    width=50, height=80
                ),
                caption=f"{i.name} \nDescription: {i.description}\nPrice:{i.price}"
            )
            update.callback_query.message.reply_text(
                "Contact business",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        text="Contact-Business-Owner",
                        callback_data=i.sme.owner.email
                    )]]
                )
            )
            print(i.sme.owner.email)
        return FETCH_SMECONTACT


def smecontact(update, context):
    data = update.callback_query.data
    data = session.query(User).filter_by(email=data).first()
    update.callback_query.message.reply_text(
        f"Telephone: {data.telephone}, "
        f"Email: {data.email}"
    )
    return


# def smedetails(update, context: CallbackContext) -> int:
#     global owner
#     user = update.message.from_user
#     # find user in db
#     name = update.message.from_user.first_name + ' ' + \
#         update.message.from_user.last_name
#     owner = session.query(User).filter_by(name=name).first()
#     owner.is_smeowner = True
#     session.commit()
#     print(msg)
#     update.message.reply_text(
#         f"Great! {user.first_name}, please tell me about your business, "
#         "provide your BrandName, Brand email, Address, and phone number"
#         "in that order, each separated by comma(,) each e.g: "
#         "JDWears, JDWears@gmail.com, 101-Mike Avenue-Ikeja, +234567897809",
#         reply_markup=ReplyKeyboardRemove()
#     )

#     return CHOOSESME_CAT


def smecat(update, context):
    # create business
    data = update.message.text.split(',')
    newbiz = Business(
        name=data[0], email=data[1],
        address=data[2], telephone=data[3],
        owner=owner
    )
    # TODO: Add checks for correct len of input data
    session.add(newbiz)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        print("Duplicate data")
        update.message.reply_text(
            "Business with email already exists, try again"
        )
        return CHOOSESME_CAT
    categories = [
        ['Clothing/Fashion', 'Hardware Accessories'],
        ['Food/Kitchen Ware', 'ArtnDesign'],
        ['Other']
    ]
    markup = ReplyKeyboardMarkup(categories, one_time_keyboard=True)
    update.message.reply_text(
        "Pick a category for your business from the options",
        reply_markup=markup
    )
    return ADD_PRODUCTS


def products(update, context):
    biz = owner.sme
    cat_ = session.query(Category).filter_by(name=update.message.text).first()
    biz.category = cat_
    session.commit()
    button = [[
        InlineKeyboardButton(
            text="Add a product",
            callback_data=biz.category.name
        )
    ]]
    update.message.reply_text(
        "Lets add some of your products - shall we>, ",
        reply_markup=InlineKeyboardMarkup(button)
    )
    return ADD_PRODUCTS


def addproduct(update, context):
    choice = update.callback_query.data
    print(choice)
    update.callback_query.message.reply_text(
        "Add the Name, Description, and Price of product, "
        "separated by commas(,) as caption to the product's image"
    )
    return ADD_PRODUCTS


def product_info(update: Update, context: CallbackContext):
    data = update.message
    print(data)
    photo = context.bot.getFile(update.message.photo[-1].file_id)
    file_ = open('product_image', 'wb')
    photo.download(out=file_)
    data = update.message.caption.split(',')
    # upload image to cloudinary
    send_photo = upload('product_image')
    # create new product
    newprod = Product(
        name=data[0], description=data[1],
        price=data[2], image=send_photo['secure_url'],
        sme=owner.sme
    )
    session.add(newprod)
    session.commit()
    button = [[InlineKeyboardButton(
        text='Add another product',
        callback_data=owner.sme.category.name
    )]]
    update.message.reply_text(
        "Added product successfully",
        reply_markup=InlineKeyboardMarkup(button)
    )
    return ADD_PRODUCTS


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states={
            CLASS_STATE: [
                MessageHandler(
                    Filters.all, classer
                )
            ],
            CHOOSING: [
                # MessageHandler(
                #     Filters.regex(r'^(SME|sme|Sme)$'), smedetails
                # ),
                # MessageHandler(
                #     Filters.regex(r'(^Customer|customer|CUSTOMER)$'),
                #     customer_details
                # )
                CallbackQueryHandler(
                    customer_details
                )
            ],
            FETCH_PREFERENCES: [
                CallbackQueryHandler(
                    fetch_preference
                )
            ],
            ADD_PRODUCTS: [
                MessageHandler(
                    Filters.regex(r'^(Clothing/Fashion|Hardware Accessories|Food/Kitchen Ware|ArtnDesign)$'),
                    products
                ),
                MessageHandler(
                    Filters.all,
                    product_info
                ),
                CallbackQueryHandler(
                    addproduct
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
            ],
            FETCH_SMECONTACT: [
                CallbackQueryHandler(
                    smecontact
                )
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
