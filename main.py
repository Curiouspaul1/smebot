from config import TOKEN, URL
from flask import Flask, request
from telegram import Bot
import telegram
from handlers import start


app = Flask(__name__)
bot = Bot(token=TOKEN)
print(bot)

@app.route(f'/{TOKEN}', methods=['POST'])
def response():
    update = telegram.Update.de_json(
        request.get_json(force=True),
        bot
    )
    start(update)
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
