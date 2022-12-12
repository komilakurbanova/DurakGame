from database import *
from game import *
from player import *
import logging
import os
import datetime as dt

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
    #TODO: Здесь должен быть код. Сколько раз и где вызывается?


def check_card(message: str, p: Player) -> Tuple[bool, str]:
    """Проверка хода на валидность
    Здесь же можно и делать ход внутри алгоритма

    Args:
        message (str): сообщение от пользователя. В идеале - 
        это текст из кнопки, т.е. нажатие на кнопку
        p1 (Player): игрок

    Returns:
        Tuple[bool, str]: 
        bool - валидность хода, 
        str - ответ из алгоритма
    """
    #TODO: Здесь должен быть код


def alg_step(p: Player, **cards) -> None:
    """Ход в алгоритме

    Args:
        p (Player): игрок
        
    В cards либо один ключ "card",
    либо два: "card" и "inline_card"
    """
    #TODO: Здесь должен быть код. Здесь нужен ещё game?


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

    # Выбрать игрока для начала
    if random.randint(0, 1):
        p2 = player.Player(user1.chat_id, user1.username)
        p1 = player.Player(user2.chat_id, user2.username)
    else:
        p1 = player.Player(user1.chat_id, user1.username)
        p2 = player.Player(user2.chat_id, user2.username)
    
    # Активные игры по уникальному ключу
    active_games[game_id] = [p1, p2, game_alg]

    # Получить две руки и два стола
    # Одно сообщение каждому из пользователей - это прислать
    # "стол" и "руку", т.е. text-message и reply-keyboards
    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_alg)

    context.bot.sent_message(chat_id=user1.chat_id, text=table1, reply_markup=hand1)
    context.bot.sent_message(chat_id=user2.chat_id, text=table2, reply_markup=hand2)


def next_iter(p1: Player, p2: Player, game_id: int, gamebot: GameTelegramBot) -> None:
    """Меняет игроков местами, ставит first_step в True 

    Args:
        p1 (_type_): _description_
        p2 (_type_): _description_
        game_id (_type_): _description_
        gamebot (_type_): _description_
    """
    active_games[game_id][0], active_games[game_id][1] = active_games[game_id][1], \
                                                         active_games[game_id][0]
    gamebot.first_step = True
    gamebot.save()


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

    username2 = player2.username
    
    # Если второй пользователь пишет сообщение,
    # он ещё неактивный, а первый защищается -
    # проверяем на желание подкинуть
    if p2.username == username and p2.active and p1.defensive:
        if message == "Подкинуть":
            # Теперь p2 активный, а p1 пассивный (но всё ещё с defensive True)
            p1.active = False
            p1.defensive = True
            p2.active = True
            p2.defensive = True

            next_iter(p1, p2, game_id, gamebot)
            
            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)

        elif message == "Завершить ход":
            p1.defensive = False
            p1.active = True
            p2.defensive = True
            p2.active = False
            
            next_iter(p1, p2, game_id, gamebot)

            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)

    # Если активный и не защищается -> нападает
    if p1.username == username and p1.active and not p1.defensive:
        # Если первое сообщение после начала атаки
        if gamebot.first_step:
            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)
            gamebot.first_step = False
            gamebot.save()
  
        elif message != "OK":
            flag_ok, alg_response = check_card(message, p1)
            if not flag_ok:
                if len(alg_response):
                    context.bot.send_message(chat_id=p1.chat_id, text=alg_response)
            else:
                alg_step(p1, {'card': message})
                ### Здесь надо присылать какие-либо сообщения после двум пользователям?
        else:
            # Если нажал кнопку ОК, то теперь p2 активный, он защищается
            p1.active = False
            p1.defensive = False
            p2.active = True
            p2.defensive = True

            next_iter(p1, p2, game_id, gamebot)
    
    # Если активный и защищается -> защищается))
    elif p1.username == username and p1.active and p1.defensive:
        if gamebot.first_step:
            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)
            gamebot.first_step = False
            gamebot.save()
  
        elif message != "OK":
            # Если в прошлый раз была inline карта
            if len(p1.last_inline_card):
                flag_ok, alg_response = check_card(message, p1)
                alg_step(p1, {'card': message, 'inline_card': p1.last_inline_card})
                p1.last_inline_card = ""
            else:
                # Не забыть убрать другие inline карты
                flag_ok, alg_response = check_card(message, p1)
                if not flag_ok:
                    if len(alg_response):
                        context.bot.send_message(chat_id=p1.chat_id, text=alg_response)
                else:
                    p1.last_inline_card = message
        else:
            
            context.bot.send_message(chat_id=p1.chat_id, text=table1, reply_markup=hand1)
            context.bot.send_message(chat_id=p2.chat_id, text=table2, reply_markup=hand2)
            # Тут мы спрашиваем, хочет ли второй игрок подкинуть карты
            # Лучше вызвать get_game_parameters


# TODO: Раскидать код из game_block соотв. функционалу: атака, защита, подкинуть. Добавить проверку на inline карту