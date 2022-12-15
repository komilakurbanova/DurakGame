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
    if len(p1.cards()) < 2:
        hand1 = cards_to_str([p1.cards()])
    else:
        hand1 = cards_to_str(p1.cards())
    if len(p2.cards()) < 2:
        hand2 = cards_to_str([p2.cards()])
    else:
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
    p1 = Player(user1.chat_id, user1.username, [])
    p2 = Player(user2.chat_id, user2.username, [])

    game_alg = Game(p1, p2)

    if p1 != game_alg.attack_player:
        p1 = game_alg.attack_player
        user1, user2 = user2, user1
    p2 = game_alg.defence_player

    p1.active = True
    p1.defensive = False
    p2.active = False
    p2.defensive = False

    game_alg.active_player = p1
    game_alg.attack_player = p1
    game_alg.defence_player = p2

    # Активные игры по уникальному ключу
    active_games[game_id] = [p1, p2, game_alg]

    # Получить две руки и два стола
    # Одно сообщение каждому из пользователей - это прислать
    # "стол" и "руку", т.е. text-message и reply-keyboards
    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_alg)
    hand_1 = []
    for i in hand1.split():
        hand_1.append([KeyboardButton(text=i)])
    hand_2 = []
    for i in hand2.split():
        hand_2.append([KeyboardButton(text=i)])

    context.bot.send_message(chat_id=user1.chat_id, text=table1, reply_markup=ReplyKeyboardMarkup(hand_1,  one_time_keyboard=True,
                                                                                                  resize_keyboard=True))
    context.bot.send_message(chat_id=user2.chat_id, text=table2, reply_markup=ReplyKeyboardMarkup(hand_2,  one_time_keyboard=True,
                                                                                                  resize_keyboard=True))


def next_iter(game_id: int, gamebot: GameTelegramBot) -> None:
    """Меняет игроков местами, ставит first_step в True

    Args:
        game_id (_type_): _description_
        gamebot (_type_): _description_
    """
    tmp1 = active_games[game_id][0]
    tmp2 = active_games[game_id][1]
    active_games[game_id] = [tmp2, tmp1, active_games[game_id][2]]
    gamebot.first_step = True
    gamebot.save()


def start_message(player1, player2, gamebot, table1, table2, hand1, hand2, context):
    if gamebot.first_step:
        context.bot.send_message(chat_id=player1.chat_id, text=table1, reply_markup=hand1)
        context.bot.send_message(chat_id=player2.chat_id, text=table2, reply_markup=hand2)
        gamebot.first_step = False
        gamebot.save()


def check_inline_card(update):
    return update.callback_query


def game_block(update, context: CallbackContext, flag_inline_card: bool) -> None:
    """Основная логика, связывающая бота и алгоритм

    Args:
        update (Update):
        context (CallbackContext):
    """
    if not flag_inline_card:
        message = update.message.text
        username = update.message.from_user.username
    else:
        username = update.message.chat.username
        message = update.data

    player1 = get_user(username)
    gamebot = get_game(player1)
    if player1 == gamebot.player1:
        player2 = gamebot.player2
    else:
        player2 = gamebot.player1
    game_id = gamebot.game_id

    p1, p2, game_obj = active_games[game_id]

    if player1.username != p1.username:
        player1, player2 = player2, player1

    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
    hand_1 = []
    for i in hand1.split():
        hand_1.append([KeyboardButton(text=i)])
    hand_2 = []
    for i in hand2.split():
        hand_2.append([KeyboardButton(text=i)])
    # TODO: написать проверку на то, пришла карта inline или нет

    # Если второй пользователь пишет сообщение,
    # он ещё неактивный, а первый защищается -
    # проверяем на желание подкинуть
    start_message(player1, player2, gamebot, table1, table2, hand_1, hand_2, context)

    if p1.username == username and p1.active and p2.defensive:
        '''может простого дурака?'''
        if message == "Подкинуть":
            # Теперь p1 активный, а p2 пассивный (но всё ещё с defensive True)
            p1.active = True
            p1.defensive = False
            p2.active = False
            p2.defensive = True
            game_obj.active_player = p1
            game_obj.attack_player = p1
            game_obj.defence_player = p2
            active_games[game_id] = p1, p2, game_obj
            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])

            hand_1.append([KeyboardButton(text="Бито")])
            context.bot.send_message(chat_id=player1.chat_id, text="Выберите, что подкидываете",
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            # context.bot.send_message(chat_id=player2.chat_id, text="{0} подкидывает!".format(p1.username),
            #                          reply_markup=ReplyKeyboardMarkup(hand_2, one_time_keyboard=True,
            #                                                           resize_keyboard=True, ))
            return

        elif message == "Бито":
            p1.defensive = True
            p1.active = False
            p2.defensive = False
            p2.active = True
            game_obj.active_player = p2
            game_obj.attack_player = p2
            game_obj.defence_player = p1
            active_games[game_id] = [p1, p2, game_obj]

            p2.take_lack_cards_from_deck(game_obj.field.deck())
            p1.take_lack_cards_from_deck(game_obj.field.deck())

            game_obj.finish_take()

            # next_iter(game_id, gamebot)

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_2 = []
            for i in hand2.split():
                hand_2.append([KeyboardButton(text=i)])
            # start_message(player1, player2, gamebot, table1, table2, hand_1, hand_2, context)

            context.bot.send_message(chat_id=player1.chat_id, text=table1,
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            context.bot.send_message(chat_id=player2.chat_id, text=table2,
                                     reply_markup=ReplyKeyboardMarkup(hand_2, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))

            unbeaten_cards = []  # передать, как inline кнопки
            for e in game_obj.field.table:
                att_c = e
                def_c = game_obj.field.table[e]
                if def_c == card.NONECARD:
                    unbeaten_cards.append(att_c)

            keyboard = []
            for card_ in unbeaten_cards:
                keyboard.append([InlineKeyboardButton(text=cards_to_str([card_]), callback_data=cards_to_str([card_]))])
            kb = InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, )

            context.bot.send_message(chat_id=player2.chat_id,
                                     text='Выберите карту, которую хотите отбить.', reply_markup=kb)

            hand_2.append([KeyboardButton(text="Взять")])
            game = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=player2.chat_id, text='Скиньте карту, которой отбиваете',
                                     reply_markup=game)

        flag_ok, alg_response = game_obj.action_possible_attack(message)
        # flag_ok, alg_response = check_card(message, p1)
        if not flag_ok:
            if len(alg_response):
                hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
                hand_1 = []
                for i in hand1.split():
                    hand_1.append([KeyboardButton(text=i)])
                hand_1.append([KeyboardButton(text="OK")])
                context.bot.send_message(chat_id=player1.chat_id, text=alg_response,
                                         reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                          resize_keyboard=True, ))
                return
        else:
            msg = make_card_from_message(message)
            game_obj.field.table[msg] = card.NONECARD
            p1.remove_card(msg)
            p1.add_attack_card(msg)

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_1.append([KeyboardButton(text="OK")])
            context.bot.send_message(chat_id=player1.chat_id, text="Скинь еще или нажми ОК",
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            return

    # Если активный и не защищается -> нападает
    if p1.username == username and p1.active and not p1.defensive:
        # Если первое сообщение после начала атаки
        if message != "OK":
            flag_ok, alg_response = game_obj.action_possible_attack(message)
            # flag_ok, alg_response = check_card(message, p1)
            if not flag_ok:
                if len(alg_response):
                    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
                    hand_1 = []
                    for i in hand1.split():
                        hand_1.append([KeyboardButton(text=i)])
                    hand_1.append([KeyboardButton(text="OK")])
                    context.bot.send_message(chat_id=player1.chat_id, text=alg_response,
                                             reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                              resize_keyboard=True, ))
                    return
            else:
                msg = make_card_from_message(message)
                game_obj.field.table[msg] = card.NONECARD
                p1.remove_card(msg)
                p1.add_attack_card(msg)

                hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
                hand_1 = []
                for i in hand1.split():
                    hand_1.append([KeyboardButton(text=i)])
                hand_1.append([KeyboardButton(text="OK")])
                context.bot.send_message(chat_id=player1.chat_id, text="Скинь еще или нажми ОК",
                                         reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                          resize_keyboard=True, ))
        else:
            # Если нажал кнопку ОК, то теперь p2 активный, он защищается
            cards = p1.attack_hand
            p2.number_of_beaten_cards = len(cards)
            p1.attack_hand = []
            # p1.take_lack_cards_from_deck(game_obj.field.deck())

            p1.active = False
            p1.defensive = False
            p2.active = True
            p2.defensive = True
            game_obj.active_player = p2
            game_obj.attack_player = p1
            game_obj.defence_player = p2

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_2 = []
            for i in hand2.split():
                hand_2.append([KeyboardButton(text=i)])

            context.bot.send_message(chat_id=player1.chat_id, text=table1, reply_markup=ReplyKeyboardMarkup(hand_1,  one_time_keyboard=True,
                                  resize_keyboard=True,))
            context.bot.send_message(chat_id=player2.chat_id, text=table2, reply_markup=ReplyKeyboardMarkup(hand_2,  one_time_keyboard=True,
                                  resize_keyboard=True,))

            unbeaten_cards = []  # передать, как inline кнопки
            for e in game_obj.field.table:
                att_c = e
                def_c = game_obj.field.table[e]
                if def_c == card.NONECARD:
                    unbeaten_cards.append(att_c)

            keyboard = []
            for card_ in unbeaten_cards:
                keyboard.append([InlineKeyboardButton(text=cards_to_str([card_]), callback_data=cards_to_str([card_]))])
            kb = InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True,)

            context.bot.send_message(chat_id=player2.chat_id,
                                     text='Выберите карту, которую хотите отбить.', reply_markup=kb)

            hand_2.append([KeyboardButton(text="Взять")])
            game = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=player2.chat_id, text='Скиньте карту, которой отбиваете', reply_markup=game)
            # TODO: выкинуть unbeaten_cards как inline под предыдущим, выкинуть hand2 как клаву


    # Если активный и защищается -> защищается))
    elif p2.username == username and p2.active and p2.defensive:
        if message != "OK" and message != "Взять":
            # Если в прошлый раз была inline карта
            if len(p2.last_inline_card) and not flag_inline_card:
                flag_ok, alg_response = game_obj.action_possible_defence(p2.last_inline_card, message)
                if not flag_ok:
                    if len(alg_response):
                        hand_2 = []
                        for i in hand2.split():
                            hand_2.append([KeyboardButton(text=i)])
                        hand_2.append([KeyboardButton(text="Взять")])
                        hand_2.append([KeyboardButton(text="OK")])
                        cards_in_hand = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
                        context.bot.send_message(chat_id=player2.chat_id, text=alg_response,
                                                 reply_markup=cards_in_hand)
                        return
                else:
                    p2.number_of_beaten_cards -= 1

                    def_c = make_card_from_message(message)
                    game_obj.field.table[make_card_from_message(p2.last_inline_card)] = def_c

                    unbeaten_cards = []  # передать, как inline кнопки
                    for e in game_obj.field.table:
                        att_c = e
                        d = game_obj.field.table[e]
                        if d == card.NONECARD:
                            unbeaten_cards.append(att_c)
                    if unbeaten_cards:
                        unbeaten_cards.remove(make_card_from_message(p2.last_inline_card))
                    p2.last_inline_card = ""
                    p2.remove_card(def_c)

                    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

                    keyboard = []
                    for card_ in unbeaten_cards:
                        keyboard.append([InlineKeyboardButton(text=cards_to_str(card_))])
                    reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                    context.bot.send_message(chat_id=player2.chat_id, text='Выберите карту, которую хотите отбивать',reply_markup=reply_markup)

                    hand_2 = []
                    for i in hand2.split():
                        hand_2.append([KeyboardButton(text=i)])
                    hand_2.append([KeyboardButton(text="Взять")])
                    hand_2.append([KeyboardButton(text="OK")])
                    cards_in_hand = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
                    context.bot.send_message(chat_id=player2.chat_id, text='Чем отобьете?', reply_markup=cards_in_hand)
                    # TODO: выкинуть unbeaten_cards как inline под предыдущим, выкинуть hand2 как клаву

            elif flag_inline_card:
                # Не забыть убрать другие inline карты
                p2.last_inline_card = message
                active_games[game_id] = [p1, p2, game_obj]

        elif message == 'OK':
            if p2.number_of_beaten_cards:
                context.bot.send_message(chat_id=player2.chat_id,
                                         text="Вы отбили не все карты! Либо отбейте, либо заберите со стола")
                return

            # p2.take_lack_cards_from_deck(game_obj.field.deck())
            p1.active = True
            p2.active = False
            p1.defensive = False
            p2.defensive = True
            game_obj.active_player = p1
            game_obj.attack_player = p1
            game_obj.defence_player = p2
            active_games[game_id] = [p1, p2, game_obj]

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_1.append([KeyboardButton(text="Бито")])
            hand_1.append([KeyboardButton(text="Подкинуть")])
            hand_2 = []
            for i in hand2.split():
                hand_2.append([KeyboardButton(text=i)])

            context.bot.send_message(chat_id=player1.chat_id, text=table1,
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            context.bot.send_message(chat_id=player2.chat_id, text=table2,
                                     reply_markup=ReplyKeyboardMarkup(hand_2, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            # Тут мы спрашиваем, хочет ли второй игрок подкинуть карты
            # Лучше вызвать get_game_parameters
        elif message == "Взять":
            game_obj.take_table(p2)
            p2.take_lack_cards_from_deck(game_obj.field.deck())
            p1.take_lack_cards_from_deck(game_obj.field.deck())

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)
            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_2 = []
            for i in hand2.split():
                hand_2.append([KeyboardButton(text=i)])
            context.bot.send_message(chat_id=player1.chat_id, text=table1,
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            context.bot.send_message(chat_id=player2.chat_id, text=table2,
                                     reply_markup=ReplyKeyboardMarkup(hand_2, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            game_obj.take_table(p2)
            next_iter(game_id, gamebot)


menu_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Игра')],
                                   [KeyboardButton(text='Статистика')],
                                   [KeyboardButton(text='Правила')],
                                   [KeyboardButton(text='Изменить имя')]],
                                  one_time_keyboard=True,
                                  resize_keyboard=True,
                                  )
# def finish_the_game(game_id, context: CallbackContext) -> None:  #что передавать
#
#     """
#     Завершение игры и определение победителя.
#     Победитель - игрок без карт при условии пустой колоды
#     Записывает в db win - пользователя-победителя из Users, end = True
#     Обнулить необходимые поля:
#     - поменять stage на wait
#     - active game id -> 0 ??
#
#     Вывести сообщение о победе и в кнопках начальное меню (игра статистика и тд)
#     """
#     p1, p2, game_obj = active_games[game_id]
#
#     winner = ''
#
#     context.bot.send_message(chat_id=player1.chat_id, text="Победил {0}, поздравляем!🎉🎉🎉 Игра окончена ".format(winner),
#                              reply_markup=menu_markup)
#     context.bot.send_message(chat_id=player2.chat_id, text="Победил {0}, поздравляем!🎉🎉🎉 Игра окончена ".format(winner),
#                              reply_markup=menu_markup)
#
#     edit_stage(p1.username, "wait")
#     edit_stage(p2.username, "wait")
#

# TODO: Раскидать код из game_block соотв. функционалу: атака, защита, подкинуть. Добавить проверку на inline карту
