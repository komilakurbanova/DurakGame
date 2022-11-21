import card
import player
import field


class Game(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        # self.field: Field = Field(p1, p2)
        # self.players:
        self.active_player: player.puid() = None
        self.defence_player: player.puid() = None
        self.field: field.Field() = None
        self.table: field.__table() = []


    def move_message(p: player.Player): # чтобы сообщить игроку что делать
                                        # это и на поле отображено, но, возможно,
                                        # такая длубликация оправдана
        message = ''
        if p.puid == Game.active_player:
            message = "Place your card!"
        elif p.puid == Game.defence_player:
            message = "The opponent is making a move, get ready to defend"
        return message


    def is_defending(self, id: player.puid):
        return self.defendce_player == id


    def is_active(self, id: player.puid):
        return self.active_player == id


    def action_possible_active(self, table: field.Field, c: card.Card):  # нам приходит ход человека и мы
                                                    # смотрим, можно ли его совершить
        verdict = False
        if table.__table.size() % 2 == 0:
            # совпадает ли карта по номиналу с теми на столе
            verdict = True
            for item in table.deck:
                if c.value != item.value:
                    verdict = False
                    break
        return verdict


    def action_possible_defence(self, table: field.Field, c: card.Card):
        verdict = False
        if table.__table.size() % 2 == 1:
            # совпадает ли карта мастью и больше ли она
            item = table.__table[-1]
            verdict = c.__gt__(item)
        return verdict


    def normal_move(c: card.Card): # игрок решает положить карту



    def take_table(self, id: player.__puid): #игрок забирает карты - defence only
        id.take_cards_from_field(Game.table)


    def finish_take(self, id: player.__puid): #бито - active only

