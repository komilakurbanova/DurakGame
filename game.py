from field import *
from typing import Tuple


class Game(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.field = Field(p1, p2)
        self.field.initialize_game()
        self.active_player = self.field.start_player
        if p1.puid() != self.active_player.puid():
            self.defence_player = p1
            self.attack_player = p2
        else:
            self.attack_player = p1
            self.defence_player = p2

    def move_message(self, p: player.Player):  # чтобы сообщить игроку что делать
        # это и на поле отображено, но, возможно,
        # такая длубликация оправдана
        message = ''
        if p.puid() == self.active_player.username():
            message = "Place your card!"
        elif p.puid() == self.defence_player.puid():
            message = "The opponent is making a move, get ready to defend"
        return message

    def is_defending(self, username: str):
        return self.defence_player.puid() == username

    def is_attacking(self, username: str):
        return self.attack_player.puid() == username

    def is_active(self, username: str):  # его ход ?
        return self.active_player.username() == username

    # проверить, что игрок вообще имеет право делать ход

    def action_possible_attack(self, message: str) -> Tuple[bool, str]:  # нам приходит ход человека и мы
        # смотрим, можно ли его совершить
        # совпадает ли карта по номиналу с теми, что на столе
        c = make_card_from_message(message)
        if not self.field.table.copy():
            return True, ''
        cur_table = list(self.field.table.copy().keys())
        cur_table += (list(self.field.table.copy().values()))
        cur_table += list(self.attack_player.attack_hand)
        set_table_vals = set()
        for x in cur_table:
            if x != card.NONECARD:
                set_table_vals.add(x.value)
        if c.value in set_table_vals:
            return True, ''
        return False, 'You cannot put this card, choose another one!'

    def action_possible_defence(self, on_table_card: str, c: str) -> Tuple[bool, str]:
        # совпадает ли карта мастью и больше ли она
        c = make_card_from_message(c)
        on_table_card = make_card_from_message(on_table_card)
        if c.suit == self.field.trump and on_table_card.suit != self.field.trump:
            return True, ''
        if c > on_table_card:
            return True, ''
        else:
            return False, "Нельзя отбить этой карту выбранную карту противника"

    def take_table(self, p: player.Player):  # игрок забирает карты - defence only
        p.take_cards_from_field(self.field.table)
        self.field.table = {}
        self.finish_take()

    def finish_take(self):  # бито - attack only, p - тот, кто бито написал
        self.field.table = {}
        self.field.players()[0].take_lack_cards_from_deck(self.field.deck())
        self.field.players()[1].take_lack_cards_from_deck(self.field.deck())

    '''
    НИЖЕ ЛОГИКА ИГРЫ 

    def normal_move(self, p: player.Player):  # игрок решает положить карту
        if not self.is_active(p.puid()):
            raise ValueError('This player must be passive')
        if self.is_attacking(p.puid()):
            # функцию, которая получит от бота список cards, которыми игрок атакует
            cards = self.player_attack_turn()
            for c in cards:
                if not self.action_possible_attack(c):
                    raise ValueError('Invalid card, choose another one')
                self.field.table[c] = card.NONECARD
                p.remove_card(c)
        if self.is_defending(p.puid()):
            unbeaten_cards = []
            for e in self.field.table:
                att_c = e
                def_c = self.field.table[e]
                if def_c == card.NONECARD:
                    unbeaten_cards.append(att_c)
            if not unbeaten_cards:
                raise ValueError('Oops, you do not need to defend')
            # функцию, которая выкинет боту неотбитые unbeaten_cards и получит от него
            # словарь dict[unbeaten, beating]
            defence = self.player_defence_turn(unbeaten_cards)
            for att_c in defence:
                def_c = defence[att_c]
                if not self.action_possible_defence(att_c, def_c):
                    raise ValueError('Invalid card, choose another one')
                self.field.table[att_c] = def_c
                p.remove_card(def_c)
        if self.active_player == self.field.players()[0]:
            self.active_player = self.field.players()[1]
        else:
            self.active_player = self.field.players()[0]
    '''


    '''
    def player_attack_turn(self):  # а должно ли это быть методом класса?
        pass
    #  return [self.attack_player.cards()[-1]]     тестирую
    def player_defence_turn(self, unbeaten_cards):  # а должно ли это быть методом класса?
        pass
    #  return {unbeaten_cards[0]: card.Card(9, 'H')}      тестирую
    '''
