def game_block(update: Update, context: CallbackContext) -> None:
    username = update.message.username
    who_attach = Game.get_attacker(username)

    if game(update.message.text):

    if who_attach:
        attack()
    else:
        defense()


def some_func_game(username1: str, username2: str, card: str, game_now: Game):
    game_girl_obj, p1, p2 = game_now.game,  game_now.p1,  game_now.p2
    girls_game(p1, p2, game_girl_obj)


def game_event(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    username1 = update.message.username
    game_now = Game.find(username1, end=False)[0]
    username2 = game_now.player2.username
    card = update.message.text

    if check_card_ok(username1, card):
         res = some_func_game(username1, username2, card, game_now)
         if res['status']:
            update.message.edit_message(reply_markup=res['hand'])
            context.bot.send_message(chat_id=username2, text=card)
            Game.set_attacker(username2)
        else:
            update.message.reply_text(text='Ты не можешь кинуть такую карту')

# --------------------------------------

import logging
import os
import datetime as dt

from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackContext



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

menu_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Игра')],
                                   [KeyboardButton(text='Статистика')],
                                   [KeyboardButton(text='Правила')],
                                   [KeyboardButton(text='Изменить имя')]],
                                  one_time_keyboard=True,
                                  resize_keyboard=True,
                                  )

game = ReplyKeyboardMarkup([[KeyboardButton(text='Игра с другом')],
                                   [KeyboardButton(text='Игра с ботом')],
                                   [KeyboardButton(text='Игра с рандомным игроком')],
                                   [KeyboardButton(text='Назад')]],
                           one_time_keyboard=True,
                           resize_keyboard=True,
                           )


cancel_markup = ReplyKeyboardMarkup([['Назад']],
                                    one_time_keyboard=True,
                                    resize_keyboard=True,
)

help_text = "Чиллим, играем, пон"


def start_block(update: Update, context: CallbackContext) -> None:
    '''
    Старт диалога.
    Args:
        update (Update)
        context (CallbackContext)
    При "/start" сразу переведёт "stage" в режим ожидания гс, 
    а также отправит шаблоны для разговора
    '''
    username = update.message.from_user.username
    # Проверяет, есть ли он в "БД"

    check_user(update)
    stage = get_stage(update)
    update.message.reply_text(f"Привет, {username}!")


def main_block(update: Update, context: CallbackContext) -> None:
    '''
    Args:
        update (Update)
        context (CallbackContext)
    Сразу переведёт "stage" в режим ожидания гс, 
    а также отправит шаблоны для разговора
    '''
    print(update.message.chat_id)
    username = update.message.from_user.username
    message = update.message.text
    check_user(update)
    stage = get_stage(update)
    if message == "Статистика":
        update.message.reply_text('Тут ничего нет)))', reply_markup=cancel_markup)
    elif message == "Правила":
        update.message.reply_text(help_text, reply_markup=cancel_markup)
    elif message == "Назад":
        update.message.reply_text("xui", reply_markup=menu_markup)
    elif message == "Игра с другом":
        edit_stage(username, "wait_game")
        update.message.reply_text("Пришли юзернейм друга")        

    elif stage == 'wait_game':
        username2 = message.split('@')[1]
        player2 = get_user(username2)
        if not len(player2):
            update.message.reply_text("Твой друг никогда не заходил в бота") 
            return
        edit_stage(username, "game")
        edit_stage(username2, "game")
        update.message.reply_text("Игра началась", reply_markup=game)  
        context.bot.send_message(chat_id=player2[0].chat_id, text='Игра началась!', reply_markup=game)
        create_game(username, username2)
    elif stage == 'game':
        game_block(update, context)


# TODO: сделать нормального бота

def main() -> None:
    updater = Updater("5885555027:AAGH0wYx4izrRgLKkicdjioladAHLAE8mHI")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_block))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          main_block))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
