from peewee import (SqliteDatabase,
                    CharField,
                    IntegerField,
                    TextField,
                    BooleanField,
                    AutoField,
                    Model,
                    ForeignKeyField,
                    DoesNotExist)

import random
from typing import Union, List

# Создание локальной БД
db = SqliteDatabase('telegram.db')
active_games = {}


class BaseModel(Model):
    class Meta:
        database = db


class Users(BaseModel):
    """Таблица пользователей.
    Args:
        BaseModel (_type_): for peewee db
    Пользователя описывает:
    username - username из API telegram
    chat_id - chat_id из API telegram
    stage - одно из состояний пользователя:
        1) menu - в меню (базовое состояние)
        2) wait_responce - Пользователь нажал на "Играть"
        3) game - Пользователь в игре
        4) new - впервые в боте, просим задать имя
        5) wait_name - ждём имя
    active_game_id - id активной игры пользователя (если в игре)
    """
    username = CharField(unique=False)
    name = CharField(unique=False, default="Аноним")
    chat_id = IntegerField(unique=True)
    stage = TextField(default="new")
    active_game_id = IntegerField(default=0)


def get_user(username: str) -> Users:
    """Найти по username пользователя
    Args:
        username (str): username из API telegram
    Returns:
        Users: найденный по username пользователь из Users
    """
    user = Users.select().where(Users.username == username)
    if len(user):
        return user.get()
    raise DoesNotExist


def add_user(chat_id: int, username: str) -> None:
    """Добавить пользователя в БД
    Args:
        chat_id (int): chat_id из API telegram
        username (str): username из API telegram
    """
    new_user = Users.create(username=username, chat_id=chat_id)
    new_user.save()


def check_user(chat_id: int, username: str) -> None:
    """Проверить пользователя в БД
    Если его там нет - добавить
    Args:
        chat_id (int): chat_id из API telegram
        username (str): username из API telegram
    """
    try:
        user = get_user(username)
    except DoesNotExist:
        add_user(chat_id, username)


def get_stage(username: str) -> Union[str, None]:
    """Получить stage пользователя
    Args:
        username (str): username из API telegram
    Returns:
        str: stage
    """
    user = get_user(username)
    return user.stage


def edit_stage(username, new_stage: str) -> None:
    """Поменять stage пользователя
    Args:
        username (_type_): username из API telegram
        new_stage (str): новый stage
    """
    user = get_user(username)
    user.stage = new_stage
    user.save()

def edit_name(username, new_name: str) -> None:
    """Поменять name пользователя
    Args:
        username (_type_): username из API telegram
        new_name (str): новый name
    """
    user = get_user(username)
    user.name = new_name
    user.save()


class GameTelegramBot(BaseModel):
    """Таблица с играми.
    Args:
        BaseModel (_type_): _description_
    Игру описывает:
    game_id - уникальный id игры
    user1, user2 - игроки класса Users с теми же атрибутами
    end - окончена ли игра (соотвественно, True/False)
    win - кто победил в игре (пользователь из Users)
    """
    game_id = AutoField()
    player1 = ForeignKeyField(Users, backref='game')
    player2 = ForeignKeyField(Users, backref='game')
    end = BooleanField(default=False)
    first_step = BooleanField(default=False)
    win = ForeignKeyField(Users, backref='game')


def create_game(user1: Users, user2: Users) -> int:
    """Запись игры
    Args:
        user1 (Users): первый игрок
        user2 (Users): второй игрок
    Returns:
        int: уникальный id игры
    """
    game = GameTelegramBot.create(player1=user1, player2=user2, win=user1)

    return game.game_id


def get_game(player: Users) -> GameTelegramBot:
    """Среди активных игр ищет игру по игроку
    Args:
        player (Users): один из двух игроков
    Returns:
        GameTelegramBot: игра
    """
    game = GameTelegramBot.select().where((GameTelegramBot.end == False) &
                                          ((GameTelegramBot.player1 == player) |
                                           (GameTelegramBot.player2 == player)))
    if len(game):
        return game.get()
    raise DoesNotExist


db.drop_tables([Users, GameTelegramBot])


db.create_tables([Users, GameTelegramBot])
