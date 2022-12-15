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

game_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Игра с другом')],
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

help_text = "Правила игры!\n" \
"Первое правила клуба дураков - любой дурак знает правила дурака.\n" \
"Ну а если серьезно, то вот они.\n\n" \
"У каждого игрока по 6 карт, первым ходит тот, у кого на руках есть меньший козырь, игра вам это сообщит." \
"На поле вы видите ваши карты, что сейчас на столе и чей ход.\n"\
"Если сейчас ваша очередь, вы можете выложить на стол карту из имеющихся на руках - будут доступны в меню. " \
            "Если выбранной картой нельзя воспользоваться, вы получите сообщение об этом - карты нужно будет" \
            " выбрать заново. После выбора нажмите/напишите ОК.\n\n" \
"Если вы ходите и стол сейчас пуст -  вы можете выложить одну карту или несколько одинакового достоинства. " \
            "Если стол не пуст и вы атакуете, то положите карты любой масти, достоинство которых совпадает с д" \
            "остоинством любой из карт, уже лежащих на столе\n\n"\
"Если вы отбиваете карты, вы должны выбрать, какую бьёте, а затем - чем бьёте из карт в меню. Отбить можно картой " \
"той же масти большего достоинства или козырем. Если нужно побить козырь - подойдёт только козырь большего номинала.\n\n"\
"Если вы хотите закончить ход в случае бито - нажмите такую кнопку. Если не можете отбиться и хотите забрать карты, нажмите взять." \
" После этого игрокам доберутся карты из колоды. Если она пуста, игра продолжиться до определения победителя."\
"Побеждает игрок, первый оставшийся без карт на руках.\n\n"\
"Приятной игры!"


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

    update.message.reply_text(f"Привет, {username}!", reply_markup=menu_markup)


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

    username = update.message.from_user.username
    message = update.message.text
    check_user(update.message.chat_id, username)
    stage = get_stage(username)

    if stage == 'game':
        game_block(update, context, flag_inline_card)
        return

    if message == "Статистика":
        update.message.reply_text(help_text, reply_markup=cancel_markup)
        # TODO: где стата?
    elif message == "Правила":
        update.message.reply_text(help_text, reply_markup=cancel_markup)

    elif message == "Назад":
        update.message.reply_text("Чего изволите теперь?", reply_markup=menu_markup)
        edit_stage(username, "new")

    elif message == "Игра":
        update.message.reply_text("Выберите тип игры", reply_markup=game_markup)

    elif message == "Игра с другом":
        edit_stage(username, "wait_responce")
        update.message.reply_text("Пришли юзернейм друга в формате @username", reply_markup=cancel_markup)

    elif message == "Игра с ботом":
        update.message.reply_text("Будет в будущих обновлениях! Сейчас доступна игра с другом", reply_markup=game_markup)

    elif message == "Игра с рандомным игроком":
        update.message.reply_text("Будет в будущих обновлениях! Сейчас доступна игра с другом", reply_markup=game_markup)

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
    updater = Updater('5739756352:AAH1NQRrgcSdsNPTcWlTyynqPHrcyA2n4Xo')
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
