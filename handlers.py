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
import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import engine, User, Business, Category, Product
import cloudinary
from cloudinary.uploader import upload
from apscheduler.schedulers.background import BackgroundScheduler
import time

Session = sessionmaker(bind=engine)
session = Session()
sched = BackgroundScheduler()

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
    CLASS_STATE, SME_DETAILS, FETCH_UPDATES, \
    CHOOSING, ADD_PRODUCTS, FETCH_SMECONTACT = range(9)

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
    if update.message.from_user.first_name is None:
        name = update.message.from_user.last_name
    elif update.message.from_user.last_name is None:
        name = update.message.from_user.first_name
    else:
        name = update.message.from_user.first_name + ' ' + \
            update.message.from_user.last_name
    print(name)
    user_ = session.query(User).filter_by(name=name).first()
    if user_ is not None:
        global owner
        owner = user_
        if user_.is_smeowner:
            if user_.sme.category:
                button = [[
                    InlineKeyboardButton(
                        text="Add new products",
                        callback_data=user_.sme.category.name
                    )
                ]]
                update.message.reply_text(
                    "Welcome back, what do you want to do",
                    reply_markup=InlineKeyboardMarkup(button)
                )
                return ADD_PRODUCTS
        else:
            global customer
            global pref
            customer = user_
            pref = customer.preference
            button = [[
                InlineKeyboardButton(
                    text="View Businesses",
                    callback_data='customer'
                )
            ]]
            update.message.reply_text(
                "Welcome back, what do you want to do",
                reply_markup=InlineKeyboardMarkup(button)
            )
            return CHOOSING
    else:
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
    #print(update.message.from_user)
    if update.message.from_user.first_name is None:
        name = update.message.from_user.last_name
    elif update.message.from_user.last_name is None:
        name = update.message.from_user.first_name
    else:
        name = update.message.from_user.first_name + ' ' + \
            update.message.from_user.last_name
    #print(name)
    data = update.message.text.split(',')
    if len(data) < 3 or len(data) > 3:
        update.message.reply_text(
            "Invalid entry, please make sure to input the details "
            "as requested in the instructions"
        )
        update.message.reply_text(
            "Type /start, to restart bot"
        )
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
        text="Collected information succesfully!..🎉🎉 \n"
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    return CHOOSING


def customer_details(update, context: CallbackContext) -> int:
    #print(update.callback_query.data.lower() == 'sme')
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
        if len(result) < 1:
            button = [[
                InlineKeyboardButton(
                    text="Select another Category?",
                    callback_data="customer"
                )
            ]]
            update.callback_query.message.reply_text(
                "Nothing here yet",
                reply_markup=InlineKeyboardMarkup(button)
            )
            return CHOOSING
        for i in result:
            button = [
                [
                    InlineKeyboardButton(
                        text='View Products',
                        callback_data=i.name
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Select for updates",
                        callback_data='pref'+','+i.name
                    )
                ]
            ]
            biz = session.query(Business).filter_by(name=i.name).first()
            #print(biz.product)
            if len(biz.product) > 0:
                ref = biz.product[0]
                #print(ref.image)
                update.callback_query.message.reply_photo(
                    photo=ref.image,
                    caption=f"{i.name}".upper(),
                    reply_markup=InlineKeyboardMarkup(button)
                )
            else:
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
            "Preference set successfully 🎉",
            reply_markup=InlineKeyboardMarkup(button)
        )
        getupdates(update, context)
        return FETCH_PREFERENCES
    else:
        choice = update.callback_query.data
        if biz:
            biz = session.query(Business).filter_by(name=choice).first().product
        if len(biz) < 1:
            button = [[
                InlineKeyboardButton(
                    text="View other businesses",
                    callback_data=biz.category.name
                )
            ]]
            update.callback_query.message.reply_text(
                "Nothing here yet",
                reply_markup=InlineKeyboardMarkup(button)
            )
            return FETCH_PREFERENCES
        for i in biz:
            update.callback_query.message.reply_photo(
                photo=i.image,
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
        biz = session.query(Business).filter_by(name=choice).first()
        button = [
            [
                InlineKeyboardButton(
                    text="View more Businesses in same category",
                    callback_data=biz.category.name
                )
            ]
        ]
        update.callback_query.message.reply_text(
            text="Done..?",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return FETCH_SMECONTACT


def smecontact(update, context):
    check = [i.name.lower() for i in session.query(Category).all()]
    print(update.callback_query.data.lower() in check)
    if update.callback_query.data.lower() in check:
        return fetch_preference(update, context)
    data = update.callback_query.data
    data = session.query(User).filter_by(email=data).first()
    update.callback_query.message.reply_text(
        f"Telephone: {data.telephone}, "
        f"Email: {data.email}"
    )
    return -1


def getupdates(update, context):
    print("Called")
    result = []
    print(result)
    pref = customer.preference.split(',')
    print(pref)
    for i in pref:
        biz = session.query(Business).filter_by(
            name=i
        ).first()
        if biz:
            item = session.query(Product).filter_by(
                name=biz.latest
            ).first()
            if item:
                result.append(item)
                biz.latest = None
                session.commit()
    if len(result) > 0:
        for i in result:
            update.callback_query.message.reply_photo(
                photo=i.image,
                caption=f"{i.sme.name}\n=========\n{i.name} \nDescription: {i.description}\nPrice:{i.price}"
            )
    else:
        update.callback_query.message.reply_text(
            "No new updates"
        )
    time.sleep(86400)
    return getupdates(update, context)


def smecat(update, context):
    # create business
    data = update.message.text.split(',')
    if len(data) < 4 or len(data) > 4:
        button = [
            [InlineKeyboardButton(
                text="Continue..",
                callback_data="sme"
            )]
        ]
        update.message.reply_text(
            "Invalid entry, please make sure to input the details "
            "as requested in the instructions",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CHOOSING
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
        "Lets add some of your products - shall we>, 🛍",
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
    send_photo = upload('product_image', width=200, height=150, crop='thumb')
    # create new product
    newprod = Product(
        name=data[0], description=data[1],
        price=data[2], image=send_photo['secure_url'],
        sme=owner.sme
    )
    session.add(newprod)
    owner.sme.latest = newprod.name
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
            ],
            FETCH_UPDATES: [
                CallbackQueryHandler(
                    getupdates
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
