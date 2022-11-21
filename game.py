import card
import player
import field


class Game(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.field = field.Field(p1, p2)
        self.field.initialize_game()
        self.active_player = self.field.start_player
        if p1.puid() != self.active_player:
            self.defence_player = p1
        else:
            self.defence_player = p2

    def move_message(self, p: player.Player):  # чтобы сообщить игроку что делать
                                        # это и на поле отображено, но, возможно,
                                        # такая длубликация оправдана
        message = ''
        if p.puid == self.active_player:
            message = "Place your card!"
        elif p.puid == self.defence_player:
            message = "The opponent is making a move, get ready to defend"
        return message

    def is_defending(self, puid: str):
        return self.defence_player.puid() == puid

    def is_active(self, puid: str):
        return self.active_player.piid() == puid

    def action_possible_active(self, c: card.Card):  # нам приходит ход человека и мы
                                                     # смотрим, можно ли его совершить
        verdict = False
        if self.field.table.size() % 2 == 0:
            # совпадает ли карта по номиналу с теми на столе
            verdict = True
            deck = self.field.deck()
            for item in deck:
                if c.value != item.value:
                    verdict = False
                    break
        return verdict

    def action_possible_defence(self, c: card.Card):
        verdict = False
        table = self.field.table
        if len(table) % 2 == 1:
            # совпадает ли карта мастью и больше ли она
            item = table[-1]
            verdict = c > item
        return verdict

    def normal_move(self, c: card.Card):  # игрок решает положить карту
        pass

    def take_table(self, p: player.Player):  # игрок забирает карты - defence only
        p.take_cards_from_field(self.field.table)

    def finish_take(self, p: player.Player):  # бито - active only
        pass
