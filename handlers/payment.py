from telebot import types
from datetime import datetime, timedelta

import logging
import json
import hashlib
import sqlite3
import requests
import threading
from urllib import parse
from urllib.parse import urlparse

import db
from init import bot
from .base import ask_amount
from utils import get_next_inv_id
from . import common as cf


# Команда /pay для Telegram бота
@bot.message_handler(commands=['pay'])
def ask_amount_base(message: types.Message):
    ask_amount(message)

