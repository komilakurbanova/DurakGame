import logging
import os
import datetime as dt

from telegram.ext import CallbackQueryHandler

from game_alg import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Вася за кнопки
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
    """
    Старт диалога.
    Args:
        update (Update)
        context (CallbackContext)
    """
    username = update.message.from_user.username

    check_user(update.message.chat_id, username)
    stage = get_stage(username)

    update.message.reply_text(f"Привет, {username}!")


def main_block(update: Update, context: CallbackContext) -> None:
    """
    Args:
        update (Update)
        context (CallbackContext)

    1) Выдает результаты по кнопкам
    2) Реализует коннект двух пользователей через game_block
    """
    flag_inline_card = check_inline_card(update)  # проверка на инлайн карtу
    if flag_inline_card:
        game_block(update.callback_query, context, flag_inline_card)
        return
    # print(update)
    username = update.message.from_user.username
    message = update.message.text
    check_user(update.message.chat_id, username)
    stage = get_stage(username)

    if stage == 'game':
        game_block(update, context, flag_inline_card)
        return

    if message == "Статистика":
        update.message.reply_text('Тут ничего нет)))', reply_markup=cancel_markup)
        # TODO: где стата?
    elif message == "Правила":
        update.message.reply_text(help_text, reply_markup=cancel_markup)
        # TODO: правила?
    elif message == "Назад":
        update.message.reply_text("Надеюсь, ты собой доволен", reply_markup=menu_markup)
    elif message == "Игра":
        edit_stage(username, "wait_responce")
        update.message.reply_text("Пришли юзернейм друга")
    elif message == "Изменить имя":
        pass
        # TODO: где?

    elif stage == 'wait_responce':
        username2 = message.split('@')[1]
        try:
            player2 = get_user(username2)
        except DoesNotExist:
            update.message.reply_text("Твой друг никогда не заходил в бота")
            return
        edit_stage(username, 'game')
        edit_stage(username2, 'game')
        new_game(username, username2, context)


def main() -> None:
    updater = Updater('5590111815:AAGP4kaHOvck-THoO_zKGvfBuAX62DvRtGk')
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_block))
    dispatcher.add_handler(CallbackQueryHandler(main_block))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          main_block))
    try:
        updater.start_polling()
        updater.idle()
    except:
        os.remove('telegram.db')


if __name__ == '__main__':
    main()

# TODO: Добавить обработку inline-кнопок, inline-кнопки и асинхронные вызовы (оптимизация запросов к бд (???))
