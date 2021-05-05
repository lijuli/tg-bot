import os
import time

import requests
import telegram
import logging
from dotenv import load_dotenv
import telegram_log_handler

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


telegram_logger = logging.getLogger(__name__)
handler = telegram_log_handler.RequestsHandler()
formatter = telegram_log_handler.LogFormatter()
handler.setFormatter(formatter)
telegram_logger.addHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(levelname)s, %(name)s, %(message)s',
    filename='telegram_bot.log',
    filemode='w'
)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
        params={'from_date': current_timestamp}
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.info(f'{bot.username} has started')
    current_timestamp = 0  # int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(
                    new_homework.get('homeworks')[0]
                )
                send_message(message, bot)
                logging.info(f'{bot.username} has sent a message')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1800)
        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            telegram_logger.error(e, exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
