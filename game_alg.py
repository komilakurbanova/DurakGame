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

menu_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Игра')],
                                   [KeyboardButton(text='Статистика')],
                                   [KeyboardButton(text='Правила')],
                                   [KeyboardButton(text='Изменить имя')]],
                                  one_time_keyboard=True,
                                  resize_keyboard=True,
                                  )


def statistics(username: str) -> str:
    """
    Статистика :)
    """
    player = get_user(username)
    games = GameTelegramBot.select().where((GameTelegramBot.end == True) &
                                           ((GameTelegramBot.player1 == player) |
                                            (GameTelegramBot.player2 == player)))
    win, lose = 0, 0
    for game in games:
        if game.win == player:
            win += 1
        else:
            lose += 1
    return f"Побед: {win}\nПоражений: {lose}\n\nВсего игр: {lose + win}"


def finish_the_game(username, context: CallbackContext, res: int) -> None:
    """
    Завершение игры и определение победителя.
    Победитель - игрок без карт при условии пустой колоды
    Записывает в db win - пользователя-победителя из Users, end = True
    Обнулить необходимые поля:
    - поменять stage на wait
    - active game id -> 0 ??
    Вывести сообщение о победе и в кнопках начальное меню (игра статистика и тд)
    """

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

    if res == 1:
        winner = p1
    else:
        winner = p2
    print(winner)
    gamebot = get_game(player1)
    gamebot.end = True
    gamebot.win = get_user(winner.username)
    gamebot.save()

    edit_stage(p1.username, "menu")
    edit_stage(p2.username, "menu")

    context.bot.send_message(chat_id=player1.chat_id,
                             text="Победил {0}, поздравляем!🎉🎉🎉 Игра окончена ".format(winner.name),
                             reply_markup=menu_markup)
    context.bot.send_message(chat_id=player2.chat_id,
                             text="Победил {0}, поздравляем!🎉🎉🎉 Игра окончена ".format(winner.name),
                             reply_markup=menu_markup)


def get_game_parameters(p1: Player, p2: Player, game_alg: Game, username, context) -> List[str]:
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

    if len(p1.cards()) != 0 and len(p1.cards()) != 0:
        return [hand1, hand2, table1, table2]
    else:
        if len(hand2) > len(hand1):  ##winner is 1
            finish_the_game(username, context, 1)
            return []
        else:
            finish_the_game(username, context, 2)
            return []


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
    p1 = Player(user1.chat_id, user1.username, [], "", user1.name)
    p2 = Player(user2.chat_id, user2.username, [], "", user2.name)

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

    if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
        return
    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_alg, username1, context)
    hand_1 = []
    for i in hand1.split():
        hand_1.append([KeyboardButton(text=i)])
    hand_2 = []
    for i in hand2.split():
        hand_2.append([KeyboardButton(text=i)])

    context.bot.send_message(chat_id=user1.chat_id, text=table1,
                             reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                              resize_keyboard=True))
    context.bot.send_message(chat_id=user2.chat_id, text=table2,
                             reply_markup=ReplyKeyboardMarkup(hand_2, one_time_keyboard=True,
                                                              resize_keyboard=True))


def next_iter(game_id: int, gamebot: GameTelegramBot) -> None:
    """Меняет игроков местами, ставит first_step в True

    Args:
        game_id (_type_): _description_
        gamebot (_type_): _description_
    """
    tmp = active_games[game_id][1]
    active_games[game_id][1] = active_games[game_id][0]
    active_games[game_id][0] = tmp
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

    if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
        return
    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)
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
    # start_message(player1, player2, gamebot, table1, table2, hand_1, hand_2, context)

    if p1.username == username and p1.active and p2.defensive:
        if message == "Подкинуть":
            # Теперь p1 активный, а p2 пассивный (но всё ещё с defensive True)
            p1.active = True
            p1.defensive = False
            p2.active = False
            p2.defensive = True
            game_obj.active_player = p1
            game_obj.attack_player = p1
            game_obj.defence_player = p2
            active_games[game_id] = [p1, p2, game_obj]
            hand_1 = []
            for i in hand1.split():
                hand_1.append([KeyboardButton(text=i)])
            hand_1.append([KeyboardButton(text="Бито")])
            context.bot.send_message(chat_id=player1.chat_id, text="Выберите, что подкидываете",
                                     reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                      resize_keyboard=True, ))
            return
        elif message == "Бито":
            p1.defensive = False
            p1.active = False
            p2.defensive = False
            p2.active = True
            game_obj.active_player = p2
            game_obj.attack_player = p2
            game_obj.defence_player = p1
            active_games[game_id] = [p1, p2, game_obj]
            game_obj.finish_take()
            if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                return

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)
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

            next_iter(game_id, gamebot)
            return
        else:
            flag_ok, alg_response = game_obj.action_possible_attack(message)
            if not flag_ok:
                if len(alg_response):
                    if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                        return
                    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)
                    hand_1 = []
                    for i in hand1.split():
                        hand_1.append([KeyboardButton(text=i)])
                    hand_1.append([KeyboardButton(text="Бито")])
                    context.bot.send_message(chat_id=player1.chat_id, text=alg_response,
                                             reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                              resize_keyboard=True, ))
                    return
            msg = make_card_from_message(message)
            game_obj.field.table[msg] = card.NONECARD
            p1.remove_card(msg)
            p1.add_attack_card(msg)
            cards = p1.attack_hand
            p2.number_of_beaten_cards = len(cards)
            p1.attack_hand = []
            p1.active = False
            p1.defensive = False
            p2.active = True
            p2.defensive = True
            game_obj.active_player = p2
            game_obj.attack_player = p1
            game_obj.defence_player = p2

            if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                return

            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)

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

            unbeaten_cards = []
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
                                     text='Выберите карту, чтобы отбить', reply_markup=kb)
            hand_2.append([KeyboardButton(text="Взять")])
            game = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=player2.chat_id, text='Скиньте карту, которой отбиваете',
                                     reply_markup=game)
        return

    # Если активный и не защищается -> нападает
    if p1.username == username and p1.active and not p1.defensive:
        # Если первое сообщение после начала атаки
        flag_ok, alg_response = game_obj.action_possible_attack(message)
        if not flag_ok:
            if len(alg_response):
                if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                    return
                hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)
                hand_1 = []
                for i in hand1.split():
                    hand_1.append([KeyboardButton(text=i)])
                context.bot.send_message(chat_id=player1.chat_id, text=alg_response,
                                         reply_markup=ReplyKeyboardMarkup(hand_1, one_time_keyboard=True,
                                                                          resize_keyboard=True, ))
                return
        else:
            msg = make_card_from_message(message)
            game_obj.field.table[msg] = card.NONECARD
            p1.remove_card(msg)
            p1.add_attack_card(msg)
            cards = p1.attack_hand
            p2.number_of_beaten_cards = len(cards)
            p1.attack_hand = []
            p1.active = False
            p1.defensive = False
            p2.active = True
            p2.defensive = True
            game_obj.active_player = p2
            game_obj.attack_player = p1
            game_obj.defence_player = p2

            if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                return
            hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)

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

            unbeaten_cards = []
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
                                     text='Выберите карту, чтобы отбить', reply_markup=kb)
            hand_2.append([KeyboardButton(text="Взять")])
            game = ReplyKeyboardMarkup(hand_2, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=player2.chat_id, text='Скиньте карту, которой отбиваете',
                                     reply_markup=game)


    # Если активный и защищается -> защищается))
    elif p2.username == username and p2.active and p2.defensive:
        try:
            if message != 'Взять':
                # Если в прошлый раз была inline карта
                if len(p2.last_inline_card) and not flag_inline_card:
                    flag_ok, alg_response = game_obj.action_possible_defence(p2.last_inline_card, message)
                    if not flag_ok:
                        if len(alg_response):
                            hand_2 = []
                            for i in hand2.split():
                                hand_2.append([KeyboardButton(text=i)])
                            hand_2.append([KeyboardButton(text="Взять")])
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

                        p1.active = True
                        p2.active = False
                        p1.defensive = False
                        p2.defensive = True
                        game_obj.active_player = p1
                        game_obj.attack_player = p1
                        game_obj.defence_player = p2
                        active_games[game_id] = [p1, p2, game_obj]

                        if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                            return
                        hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)

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

                elif flag_inline_card:
                    # Не забыть убрать другие inline карты
                    p2.last_inline_card = message
                    active_games[game_id] = [p1, p2, game_obj]
            elif message == "Взять":
                p1.active = True
                p2.active = False
                p1.defensive = False
                p2.defensive = True

                game_obj.take_table(p2)

                game_obj.active_player = p1
                game_obj.attack_player = p1
                game_obj.defence_player = p2

                active_games[game_id] = [p1, p2, game_obj]

                context.bot.send_message(chat_id=player1.chat_id, text='Противник взял стол')
                context.bot.send_message(chat_id=player2.chat_id, text='Вы взяли стол. Ой...')

                if get_stage(p1.username) == "wait" or get_stage(p2.username) == "wait":
                    return
                hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj, username, context)
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
        except:
            context.bot.send_message(chat_id=player2.chat_id,
                                     text='Вы точно жмакнули на карту соперника, а потом прислали свою карту?')
            return
