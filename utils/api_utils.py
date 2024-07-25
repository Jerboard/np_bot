from telebot import types
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip
from PIL import Image

import logging
import re
import os
import json
import hashlib
import sqlite3
import requests
import threading
from urllib import parse
from flask import Flask, request, redirect

import db
from init import bot, app


@app.route('/result', methods=['GET'])
def payment_result():
    request_data = request.query_string.decode('utf-8')
    result = result_payment(mrh_pass2, request_data)

    if "OK" in result:
        inv_id = result.replace("OK", "")
        conn = sqlite3.connect('bot_database2.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE payments SET status = ? WHERE inv_id = ?', ('paid', inv_id))
        conn.commit()
        # Получение chat_id для отправки уведомления
        cursor.execute('SELECT chat_id, amount FROM payments WHERE inv_id = ?', (inv_id,))
        row = cursor.fetchone()
        chat_id = row[0]
        amount = row[1]
        cursor.execute('UPDATE users SET balance = balance + ?, total_balance = total_balance + ? WHERE chat_id = ?', (amount, amount, chat_id))
        conn.commit()
        conn.close()

        # Оповещение пользователя о подтверждении оплаты
        bot.send_message(chat_id, f"Оплата подтверждена для счета: {inv_id}. Спасибо за ваш платеж!")

    return result

@app.route('/success', methods=['GET'])
def payment_success():
    request_data = request.query_string.decode('utf-8')
    result = check_success_payment(mrh_pass1, request_data)
    return result

def get_next_inv_id(chat_id):
    # Логика для получения следующего уникального inv_id
    last_inv_id = db.query_db('SELECT MAX(inv_id) FROM payments WHERE chat_id = ?', (chat_id,), one=True)
    return (int(last_inv_id[0]) if last_inv_id[0] is not None else 0) + 1