db = SqliteDatabase('telegram.db')
active_games = {}

class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=False)
    chat_id = IntegerField(unique=True)
    stage = TextField(default="New")
    game_id_active = IntegerField(default=0)



def get_user(username):
    return User.select().where(User.username == username)


def add_user(chat_id, username):
    new_user = User.create(username=username, chat_id=chat_id)
    new_user.save()

    
def check_user(update: Update) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    user = get_user(username)
    if not len(user):
        add_user(chat_id, username)


def get_stage(user: Update.effective_user) -> str:
    user = get_user(user.username)
    if len(user):
       return user[0].stage


def edit_stage(username, new_stage: str) -> None:
    user = get_user(username)
    if len(user):
        user = user[0]
        user.stage = new_stage
        user.save()


class GameTelegramBot(BaseModel):
    game_id = AutoField()
    username_1 = CharField(unique=False)
    username_2 = CharField(unique=False)
    chat_id_1 = IntegerField(unique=True)
    chat_id_2 = IntegerField(unique=True)
    end = BooleanField(default=False)
    win = CharField(default='')
    last_step = CharField(default='')


def create_game(username1, username2):
    
    user1 = get_user(username1)
    user2 = get_user(username2)

    id1, id2 = user1.chat_id, user2.chat_id
    username1, username2 = user1.username, user2.username

    game = GameTelegramBot.create(username_1=username1, username_2=username2,
                                  chat_id_1=id1, chat_id_2=id2)

    game_id = game.game_id

    p1 = Player(user1, 'first', [])
    p2 = Player(user2, 'second', [])

    game_alg = Game(p1, p2)

    active_games[game_id] = [p1, p2, game_alg]

    edit_stage(user1, "playing")
    edit_stage(user2, "playing")
    
    
#    --------------------------------


from peewee import (SqliteDatabase,
                    CharField,
                    IntegerField,
                    TextField,
                    BooleanField,
                    AutoField,
                    Model)

import random


db = SqliteDatabase('telegram.db')
active_games = {}


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=False)
    chat_id = IntegerField(unique=True)
    stage = TextField(default="New")
    game_id_active = IntegerField(default=0)


def get_user(username):
    return User.select().where(User.username == username)


def add_user(chat_id, username):
    new_user = User.create(username=username, chat_id=chat_id)
    new_user.save()

    
def check_user(update) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    user = get_user(username)
    if not len(user):
        add_user(chat_id, username)


def get_stage(update: Update) -> str:
    user = get_user(update.message.from_user.username)
    if len(user):
       return user[0].stage


def edit_stage(username, new_stage: str) -> None:
    user = get_user(username)
    if len(user):
        user = user[0]
        user.stage = new_stage
        user.save()


class GameTelegramBot(BaseModel):
    game_id = AutoField()
    username_1 = CharField(unique=False)
    username_2 = CharField(unique=False)
    chat_id_1 = IntegerField(unique=True)
    chat_id_2 = IntegerField(unique=True)
    end = BooleanField(default=False)
    win = CharField(default='')

    # Перед началом атаки или защиты переходит в False
    # В конце каждой атаки или защиты (перед переходом хода)
    # Переходит в True
    first_step = BooleanField(default=True)


class Player:
    """
    Заглушка
    """
    active = False
    defensive = False
    username = "alexxez13"
    last_inline_card = ""

def create_game(username1, username2):
    
    user1 = get_user(username1)[0]
    user2 = get_user(username2)[0]

    id1, id2 = user1.chat_id, user2.chat_id
    username1, username2 = user1.username, user2.username

    game = GameTelegramBot.create(username_1=username1, username_2=username2,
                                  chat_id_1=id1, chat_id_2=id2)

    game_id = game.game_id

    p1 = Player()
    p2 = Player()

    game_alg = Game(p1, p2)

    active_games[game_id] = [p1, p2, game_alg]
    
    if random.randint(0, 1):
        start_username = username1
        p1.active = True
    else:
        start_username = username2
        p2.active = True
        active_games[game_id] = [p2, p1, game_alg]

    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_alg)

    context.bot.sent_message(chat_id=id1, text=f"Начинает {start_username}\n" + table1, reply_markup=hand1)
    context.bot.sent_message(chat_id=id2, text=f"Начинает {start_username}\n" + table2, reply_markup=hand2)

    edit_stage(user1, "playing")
    edit_stage(user2, "playing")

    

def get_game(chat_id):
    game = GameTelegramBot.select().where((GameTelegramBot.end == False) & 
                                          ((GameTelegramBot.chat_id_1 == chat_id) | 
                                           (GameTelegramBot.chat_id_2 == chat_id)))
    return game
    

db.create_tables([User, GameTelegramBot])  


# ------------------------------
def check_card(message, chat_id, username, player):
    """
    Returns:
        Flag - OK или не OK всё прошло, валидность карты
        Message - Если что-то нужно дополнительно сообщить
    """
    return (True, "")


def next_iter(p1, p2, game_id, gamebot):
    active_games[game_id][0], active_games[game_id][1] = active_games[game_id][1], \
                                                         active_games[game_id][0]
    gamebot.first_step = True
    gamebot.save()

def game_block(update: Update, context: CallbackContext) -> None:
    message = update.message.text

    username1 = update.message.from_user.username
    chat_id1 = update.message.chat_id
    
    gamebot = get_game(chat_id1).get()
    game_id = gamebot.game_id

    p1, p2, game_obj = active_games[game_id]

    hand1, hand2, table1, table2 = get_game_parameters(p1, p2, game_obj)

    chat_id2 = p2.chat_id
    username2 = p2.username

    if p2.username == username1 and p1.active and p1.defensive:
        if message == "Подкинуть":
            p2.active = True
            p1.active = False
            
            next_iter(p1, p2, game_id, gamebot)
            
            context.bot.send_message(chat_id=chat_id1, text=f'Атакует {username1}')
            context.bot.send_message(chat_id=chat_id2, text=f'Защищается {username2}')

        elif message == "Завершить ход":
            p1.defensive = False
            p2.defensive = True
            p1.active = True
            p2.active = False
            
            next_iter(p1, p2, game_id)

            context.bot.send_message(chat_id=chat_id1, text=f'Защищается {username1}')
            context.bot.send_message(chat_id=chat_id2, text=f'Атакует {username2}')

    if p1.username == username1 and p1.active and not p1.defensive:
        if gamebot.first_step:
            context.bot.send_message(chat_id=chat_id1, text=f'Атакует {username1}')
            context.bot.send_message(chat_id=chat_id2, text=f'Защищается {username2}')
            gamebot.first_step = False
            gamebot.save()
  
        elif message != "OK":
            flag_ok, alg_response = check_card(message, chat_id1, username1, p1)
            if not flag_ok:
                if len(alg_response):
                    context.bot.send_message(chat_id=chat_id1, text=alg_response)
            else:
                step_one_card(message, chat_id1, username1, p1)
        else:
            p1.active = False
            p2.active = True
            p2.defensive = True

            next_iter(p1, p2, game_id, gamebot)

    elif p1.username == username1 and p1.active and p1.defensive:
        if gamebot.first_step:
            context.bot.send_message(chat_id=chat_id1, text=f'Защищается {username1}')
            context.bot.send_message(chat_id=chat_id2, text=f'Атакует {username2}')
            gamebot.first_step = False
            gamebot.save()
  
        elif message != "OK":
            if len(p1.last_inline_card):
                flag_ok, alg_response = check_card(message, chat_id1, username1, p1)
                step_two_card(message, p1.last_inline_card, chat_id1, username1, p1)
                p1.last_inline_card = ""
            else:
                # Не забыть убрать другие inline карты
                flag_ok, alg_response = check_card(message, chat_id1, username1, p1)
                if not flag_ok:
                    if len(alg_response):
                        context.bot.send_message(chat_id=chat_id1, text=alg_response)
                else:
                    p1.last_inline_card = message

            if not flag_ok:
                if len(alg_response):
                    context.bot.send_message(chat_id=chat_id1, text=alg_response)
            else:
                step_one_card(message, chat_id1, username1, p1)
        else:
            # Манипуляции с картами на столе и в руках
            defense_step(game_obj)
            context.bot.send_message(chat_id=chat_id1, text="Ждём ответ второго игрока")
            context.bot.send_message(chat_id=chat_id2, text="Хотите подкинуть?")

