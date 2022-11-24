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

    def is_attacking(self, puid: str):
        return self.defence_player.puid() != puid

    def is_active(self, puid: str):  # его ход ?
        return self.active_player.piid() == puid

    # проверить, что игрок вообще имеет право делать ход

    def action_possible_attack(self, c: card.Card):  # нам приходит ход человека и мы
        # смотрим, можно ли его совершить
        # совпадает ли карта по номиналу с теми, что на столе
        cur_table = self.field.table.keys()
        cur_table.append(self.field.table.values())
        set_table_vals = {x.value for x in cur_table}
        if c.value in set_table_vals:
            return True
        return False

    def action_possible_defence(self, on_table_card: card.Card, c: card.Card):
        # совпадает ли карта мастью и больше ли она
        return c > on_table_card

    def normal_move(self, p: player.Player):  # игрок решает положить карту
        if not self.is_active(p.puid()):
            raise ValueError('This player must be passive')
        if self.is_attacking(p.puid()):
            # функцию, которая получит от бота список cards, которыми игрок атакует

            cards = self.player_attack_turn()

            for c in cards:
                if not self.action_possible_attack(c):
                    raise ValueError('Invalid card, choose another one')
                self.field.table.append(c)
                p.remove_card(c)

        if self.is_defending(p.puid()):
            unbeaten_cards = []
            for [att_c, def_c] in self.field.table:
                if not def_c:
                    unbeaten_cards.append(att_c)
            if not unbeaten_cards:
                raise ValueError('Oops, you do not need to defend')
            # функцию, которая выкинет боту неотбитые unbeaten_cards и получит от него
            # словарь dict[unbeaten, beating]

            defence = self.player_defence_turn(unbeaten_cards)

            for [att_c, def_c] in defence:
                if not self.action_possible_defence(att_c, def_c):
                    raise ValueError('Invalid card, choose another one')
                self.field.table.append(def_c)
                p.remove_card(att_c)

    def take_table(self, p: player.Player):  # игрок забирает карты - defence only
        if not self.is_defending(p.puid()):
            raise ValueError('This player cannot take cards')
        p.take_cards_from_field(self.field.table)
        self.field.table = {}

<<<<<<< HEAD
    def finish_take(self, p1: player.Player, p2: player.Player):  # бито - attack only, p - тот, кто бито написал
        if self.defence_player.puid() == p1.puid():
            self.defence_player = p1.puid()
        else:
            self.defence_player = p2.puid()

=======
    def finish_take(self, p: player.Player):  # бито - attack only
        # не пон, а что тут ? ? ?
>>>>>>> 41b0335875a2081e9f12a83fa2738be983f4b125
        self.field.table = {}
        pass

    def player_attack_turn(self):  # а должно ли это быть методом класса?
        pass

    def player_defence_turn(self, unbeaten_cards):  # а должно ли это быть методом класса?
        pass
