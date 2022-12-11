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
