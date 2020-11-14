from config import TOKEN, URL
from flask import Flask, request
from telegram import Bot
import telegram
from handlers import main, updater, start_handler
# from telegram.ext import Dispatcher


app = Flask(__name__)
bot = Bot(token=TOKEN)


@app.route(f'/{TOKEN}', methods=['POST'])
def response():
    """update = telegram.Update.de_json(
        request.get_json(force=True),
        bot
    )"""
    main()
    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def setWebhook():
    s = bot.setWebhook(f"{URL}{TOKEN}")
    if s:
        return "set webhook successfully"
    else:
        return "webhook not set!"


if __name__ == "__main__":
    app.run(threaded=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(start_handler)
    updater.start_webhook(
        listen='0.0.0.0',
        url_path=TOKEN
    )
    updater.bot.set_webhook(
        URL + TOKEN
    )
