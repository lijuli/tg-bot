import os
import time

import requests
import telegram
import logging
import telegram_log_handler

PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
PRAKTIKUM_API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
SLEEP_TIMEOUT = 1800
ERR_SLEEP_TIMEOUT = 600
VERDICTS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Ревьюер начал ревью.',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.')
}

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

    if not homework_name or not homework_status:
        logging.error('homework_name is %s', homework_name)
        logging.error('homework_status is %s', homework_status)
        return 'Не удалось получить данные о работе.'

    if homework_status not in VERDICTS:
        logging.error('Unexpected status of homework: %s', homework_status)
        return f'Статус работы: {homework_status}'

    return (f'У вас проверили работу "{homework_name}"!\n\n'
            f'{VERDICTS.get(homework_status)}')


def check_json(response):
    response_json = response.json()
    if 'error' in response_json:
        logging.error('Error in response')
        raise Exception('Error in response: %s', response_json.get('error'))
    return response_json


def get_homework_statuses(current_timestamp):
    try:
        response = requests.get(
            url=PRAKTIKUM_API,
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp}
        )
        # response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(e, exc_info=True)
        raise e
    return check_json(response)


def send_message(message, bot_client=None):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except telegram.TelegramError as e:
        logging.error(e, exc_info=True)
        raise e


def main():
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logging.info(f'{bot.username} has started')
    except telegram.TelegramError as e:
        logging.error(e, exc_info=True)
        raise e
    current_timestamp = int(time.time())

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
            time.sleep(SLEEP_TIMEOUT)
        except Exception as e:
            telegram_logger.error(e, exc_info=True)
            time.sleep(ERR_SLEEP_TIMEOUT)


if __name__ == '__main__':
    main()
