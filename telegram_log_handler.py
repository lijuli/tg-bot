import datetime as dt
import os
from logging import Formatter
from logging import Handler

import requests


TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']


class RequestsHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        payload = {
            'chat_id': CHAT_ID,
            'text': log_entry,
        }
        return requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            data=payload
        ).content


class LogFormatter(Formatter):

    def format(self, record):
        _date_format = '%d.%m.%Y'
        date = dt.datetime.utcnow().strftime(_date_format)
        return f'{date}: {record.msg}'
