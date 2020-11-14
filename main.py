from config import TOKEN, URL
from flask import Flask, request
from telegram import Bot
import telegram
from handlers import main, start
from telegram.ext import Dispatcher, CommandHandler
from queue import Queue


app = Flask(__name__)
bot = Bot(token=TOKEN)
queue = Queue()

start_handler = CommandHandler('start', start)


@app.route(f'/{TOKEN}', methods=['POST'])
def response():
    update = telegram.Update.de_json(
        request.get_json(force=True),
        bot
    )
    for i in update:
        try:
            queue.put(i)
        except Queue.Empty:
            print('All results loaded from result_queue')
            pass
    dispatcher = Dispatcher(bot, update_queue=queue)
    dispatcher.add_handler(start_handler)
    # start(update)
    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def setWebhook():
    s = bot.setWebhook(f"{URL}{TOKEN}")
    if s:
        return "set webhook successfully"
    else:
        return "webhook not set!"


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
