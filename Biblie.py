from LxmlSoup import LxmlSoup
import telebot
import sqlite3
import requests
import datetime
import schedule
import time
from threading import Thread

bot = telebot.TeleBot('YOUR_TOKEN_HERE')
def get_db_connection():
    return sqlite3.connect('Direct to database', check_same_thread=False)


def db_table_val(user_id: int, user_name: str, username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Database (user_id, user_name, username) VALUES (?, ?, ?)', (user_id, user_name, username))
    conn.commit()
    conn.close()

def db_sub(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Subscribers (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def db_sub_del(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Subscribers WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def db_check(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    us_id = message.from_user.id
    if cursor.execute("SELECT user_id FROM Database WHERE user_id = ?", (us_id,)).fetchone() is None:
        us_name = message.from_user.first_name
        username = message.from_user.username
        db_table_val(user_id=us_id, user_name=us_name, username=username)
    conn.close()

def hp(call):
    bot.send_message(call.from_user.id, "Список доступных команд:\n\
/hi - Поздороваться!\n\
/quote - Случайная цитата из Библии\n\
/help - Вызывает список доступных команд\n\
/notifications - Проверка подписки на уведомления")

def send_daily_quote():
    print("send_daily_quote called")
    html = requests.get("https://dailyverses.net/ru/").text
    soup = LxmlSoup(html)
    Quote = soup.find_all("span", class_="v2")[0].text()
    Location = soup.find_all("a", class_="vc")[1].text()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Subscribers")
    subscribers = cursor.fetchall()
    
    for subscriber in subscribers:
        bot.send_message(subscriber[0], f"Случайный стих: “{Quote}” — {Location}")
    
    conn.close()
    print("Messages sent to all subscribers")

def schedule_checker():
    print("Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule.every().day.at("08:00").do(send_daily_quote)
print(schedule.get_jobs())

thread = Thread(target=schedule_checker)
thread.start()

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    db_check(message)
    if message.text == "/hi" or message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Список доступных команд:\n\
/hi - Поздороваться!\n\
/quote - Случайная цитата из Библии\n\
/help - Вызывает список доступных команд\n\
/notifications - Проверка подписки на уведомления")
    elif message.text == "/quote":
        html = requests.get("https://dailyverses.net/ru/").text
        soup = LxmlSoup(html)
        Quote = soup.find_all("span", class_="v2")[0].text()
        Location = soup.find_all("a", class_="vc")[1].text()
        bot.send_message(message.from_user.id, f"Случайный стих : “{Quote}”  —  {Location}")
        
    elif message.text == "/notifications":
        global ultimate_us_id 
        ultimate_us_id = us_id = message.from_user.id
        
        conn = get_db_connection()
        cursor = conn.cursor()
        if cursor.execute("SELECT user_id FROM Subscribers WHERE user_id = ?", (us_id,)).fetchone() is None:
            inline_yes = telebot.types.InlineKeyboardButton("Да", callback_data = "Yes")
            inline_no = telebot.types.InlineKeyboardButton("Нет", callback_data = "No")
            inline_keyboard = telebot.types.InlineKeyboardMarkup()
            inline_keyboard.add(inline_yes)
            inline_keyboard.add(inline_no)
            bot.send_message(message.from_user.id, "Вы хотите подключить уведомления?", reply_markup=inline_keyboard)
        else:
            inline_yes2 = telebot.types.InlineKeyboardButton("Да", callback_data = "Yes2")
            inline_no2 = telebot.types.InlineKeyboardButton("Нет", callback_data = "No2")
            inline_keyboard2 = telebot.types.InlineKeyboardMarkup()
            inline_keyboard2.add(inline_yes2)
            inline_keyboard2.add(inline_no2)
            bot.send_message(message.from_user.id, "У вас уже есть подписка на уведомления, хотите отказаться от неё?", reply_markup=inline_keyboard2)
        conn.close()
    else:
        bot.send_message(message.from_user.id, "Используй команды из перечня. Чтобы увидеть перечень команды - пиши /help.")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "Yes":
        db_sub(user_id=ultimate_us_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Уведомления успешно подключены! Рассылка каждый день в 8 утра")
        hp(call)
    elif call.data == "No":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        hp(call)
    elif call.data == "Yes2":
        db_sub_del(user_id=ultimate_us_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Вы всё дальше от Бога...")
        hp(call)
    elif call.data == "No2":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        hp(call)

bot.polling(none_stop=True, interval=0)
