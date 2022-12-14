from database import *
from game import *
from player import *
from field import *
import logging
import os
import datetime as dt
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram import (Update,
                      ReplyKeyboardRemove,
                      ReplyKeyboardMarkup,
                      KeyboardButton)

from telegram.ext import (Updater,
                          CommandHandler,
                          MessageHandler,
                          Filters,
                          CallbackContext)


def get_game_parameters(p1: Player, p2: Player, game_alg: Game) -> List[str]:
    """_summary_

    Args:
        p1 (Player): some
        p2 (Player): some
        game_alg (Game): some

    Returns:
        List[str]: hand1, hand2, table1, table2
        hand1, hand2 - рука первого и второго игрока
        table1, table2 - сообщения, которые пойдут игрокам
    """
    hand1 = cards_to_str(p1.cards())
    hand2 = cards_to_str(p2.cards())
    table1 = game_alg.field.field_view_for_player(p1, game_alg.active_player)
    table2 = game_alg.field.field_view_for_player(p2, game_alg.active_player)
    return [hand1, hand2, table1, table2]


def new_game(username1: str, username2: str, context: CallbackContext) -> None:
    """Создаем игру.

    Args:
        username1 (_type_): username первого игрока
        username2 (_type_): username второго игрока
    """
    user1 = get_user(username1)
    user2 = get_user(username2)

    game_id = create_game(user1, user2)

    # Создаем игроков для дурака
    p1 = Player(user1.chat_id, user1.username)
    p2 = Player(user2.chat_id, user2.username)

    game_alg = Game(p1, p2)

    p1 = game_alg.attack_player
    p1.active = True
    p1.defensive = False

    p2 = game_alg.defence_player
    p2.active = False
    p2.defensive = True

    # Активные игры по уникальному ключу
    active_games[game_id] = [p1, p2, game_alg]

    # Получить две руки и два стола
    # Одно сообщение каждому из пользователей - это прислать
    # "стол" и "руку", т.е. text-message и reply-keyboards
    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_alg)

    context.bot.send_message(chat_id=user1.chat_id, text=table1, reply_markup=hand1)
    context.bot.send_message(chat_id=user2.chat_id, text=table2, reply_markup=hand2)


def next_iter(game_id: int, gamebot: GameTelegramBot) -> None:
    """Меняет игроков местами, ставит first_step в True

    Args:
        game_id (_type_): _description_
        gamebot (_type_): _description_
    """
    active_games[game_id][0], active_games[game_id][1] = active_games[game_id][1], active_games[game_id][0]
    gamebot.first_step = True
    gamebot.save()


def start_message(p1, p2, gamebot, table1, table2, hand1, hand2, context):
    if gamebot.first_step:
        context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
        context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)
        gamebot.first_step = False
        gamebot.save()


def check_inline_card(update, message):
    if update.callback_query is not None and "callback_query" in update.callback_query:
        return True
    return False


def game_block(update: Update, context: CallbackContext) -> None:
    """Основная логика, связывающая бота и алгоритм

    Args:
        update (Update):
        context (CallbackContext):
    """
    message = update.message.text
    username = update.message.from_user.username
    player1 = get_user(username)
    gamebot = get_game(player1)
    game_id = gamebot.game_id
    player2 = gamebot.player2

    p1, p2, game_obj = active_games[game_id]

    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

    flag_inline_card = check_inline_card(update, message)  # проверка на инлайн карtу
    # TODO: написать проверку на то, пришла карта inline или нет

    # Если второй пользователь пишет сообщение,
    # он ещё неактивный, а первый защищается -
    # проверяем на желание подкинуть
    start_message(p1, p2, gamebot, table1, table2, hand1, hand2, context)
    
    if p1.name == username and p1.active and p2.defensive:
        '''может простого дурака?'''
        if message == "Подкинуть":
            # Теперь p1 активный, а p2 пассивный (но всё ещё с defensive True)
            p1.active = True
            p1.defensive = False
            p2.active = False
            p2.defensive = True

            context.bot.send_message(chat_id=p1.chat_id, text="Выберите, что подкидываете", reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text="{0} подкидывает!".format(p1.name), reply_markup=hand2)

        elif message == "Бито":
            p1.defensive = True
            p1.active = False
            p2.defensive = False
            p2.active = True
           # gamebot.first_step = False   это в next_step
            game_obj.finish_take()
            start_message(p1, p2, gamebot, table1, table2, hand1, hand2, context)
            next_iter(game_id, gamebot)

            # context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            # context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)

    # Если активный и не защищается -> нападает
    if p1.name == username and p1.active and not p1.defensive:
        # Если первое сообщение после начала атаки
        if message != "OK":
            flag_ok, alg_response = game_obj.action_possible_attack(message)
            # flag_ok, alg_response = check_card(message, p1)
            if not flag_ok:
                if len(alg_response):
                    context.bot.send_message(chat_id=p1.chat_id, text=alg_response)
                    return
            else:
                p1.add_attack_card(make_card_from_message(message))
                p1.active = False
                p2.active = True
                p1.defensive = False
                p2.defensive = True
                #alg_step(p1, {'card': message})
                ### Здесь надо присылать какие-либо сообщения после двум пользователям?
        else:
            # Если нажал кнопку ОК, то теперь p2 активный, он защищается
            cards = p1.attack_hand
            p2.number_of_beaten_cards = len(cards)
            for c in cards:
                game_obj.field.table[c] = card.NONECARD
                p1.remove_card(c)
            p1.attack_hand = []

            p1.active = False
            p1.defensive = False
            p2.active = True
            p2.defensive = True

           # next_iter(game_id, gamebot)
            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)

            unbeaten_cards = []  # передать, как inline кнопки
            for e in game_obj.field.table:
                att_c = e
                def_c = game_obj.field.table[e]
                if def_c == card.NONECARD:
                    unbeaten_cards.append(att_c)
            context.bot.send_message(chat_id=p2.chat_id, text='Выберите карту, которую хотите отбить. Скиньте карту,'
                                                              ' которой отбиваете')

            keyboard = []
            for card_ in unbeaten_cards:
                keyboard.append([InlineKeyboardButton(text=str(card_))])
            reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=p2.chat_id, reply_markup=reply_markup)

            hand_2 = []
            for i in hand2.split():
                hand_2.append([KeyboardButton(text=i)])
            hand_2.append([KeyboardButton(text="Взять")])
            game = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=p2.chat_id, reply_markup=game)
            # TODO: выкинуть unbeaten_cards как inline под предыдущим, выкинуть hand2 как клаву


    # Если активный и защищается -> защищается))
    elif p2.name == username and p2.active and p2.defensive:
        if message != "OK":
            # Если в прошлый раз была inline карта
            if len(p1.last_inline_card) and not flag_inline_card:
                flag_ok, alg_response = game_obj.action_possible_defence(p2.last_inline_card, message)
                if not flag_ok:
                    if len(alg_response):
                        context.bot.send_message(chat_id=p2.chat_id, text=alg_response)
                        return
                else:
                    p2.number_of_beaten_cards -= 1
                    def_c = make_card_from_message(message)
                    game_obj.field.table[make_card_from_message(p2.last_inline_card)] = def_c

                    unbeaten_cards = []  # передать, как inline кнопки
                    for e in game_obj.field.table:
                        att_c = e
                        def_c = game_obj.field.table[e]
                        if def_c == card.NONECARD:
                            unbeaten_cards.append(att_c)
                    unbeaten_cards.remove(make_card_from_message(p2.last_inline_card))
                    p2.last_inline_card = ""
                    p2.remove_card(def_c)

                    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

                    context.bot.send_message(chat_id=p2.chat_id,
                                             text='Выберите карту, которую хотите отбить. Скиньте карту,'
                                                  ' которой отбиваете', )

                    keyboard = []
                    for card_ in unbeaten_cards:
                        keyboard.append([InlineKeyboardButton(text=str(card_))])
                    reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                    context.bot.send_message(chat_id=p2.chat_id, reply_markup=reply_markup)

                    hand_2 = []
                    for i in hand2.split():
                        hand_2.append([KeyboardButton(text=i)])
                    hand_2.append([KeyboardButton(text="Взять")])
                    cards_in_hand = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
                    context.bot.send_message(chat_id=p2.chat_id, reply_markup=cards_in_hand)
                    # TODO: выкинуть unbeaten_cards как inline под предыдущим, выкинуть hand2 как клаву

            elif flag_inline_card:
                # Не забыть убрать другие inline карты
                p2.last_inline_card = message

        elif message == 'OK':
            if p2.number_of_beaten_cards:
                context.bot.send_message(chat_id=p2.chat_id, text="Вы отбили не все карты! Либо отбейте, либо заберите со стола")
                return

            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)
            p1.active = True
            p2.active = False
            p1.defensive = False
            p2.defensive = True
            # Тут мы спрашиваем, хочет ли второй игрок подкинуть карты
            # Лучше вызвать get_game_parameters
        elif message == "Взять":
            game_obj.take_table(p2)
            next_iter(game_id, gamebot)

# TODO: Раскидать код из game_block соотв. функционалу: атака, защита, подкинуть. Добавить проверку на inline карту
