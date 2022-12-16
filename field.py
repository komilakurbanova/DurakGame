import card
import player
from typing import List, Dict
import random

suit_to_emoji = {'SPADES': '♠', 'CLUBS': '♣', 'DIAMONDS': '♦', 'HEARTS': '♥', 'NONEXIST': ''}
emoji_to_suit = {'♠': 'S', '♣': 'C', '♦': 'D', '♥': 'H', '': 'N'}

extra = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}


def make_card_from_message(message: str):
    message = message.strip()
    if message[:-1] in extra:
        value = extra[message[:-1]]
    else:
        value = int(message[:-1])
    suit = card.Card.Suit(emoji_to_suit[message[-1]])
    return card.Card(value, suit)


def generate_deck():
    sample_deck = [card.Card(val, suit) for val in range(6, 15) for suit in ['S', 'C', 'D', 'H']]
    return sample_deck


def cards_to_str(cards: List[card.Card]):
    ret = ""
    for c in cards:
        ret += ("{0}{1}".format(c.value_str(), suit_to_emoji[c.suit.name])) + ' '
    return ret


class Field(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.__players = [p1, p2]
        self.__deck = []
        self.trump = None
        self.table = dict()
        self.start_player = self.__players[0]

    def add_attack_card(self, c: card.Card, p: player.Player):
        players = self.players()
        if players[0].puid() == p.puid():
            self.__players[0].attack_hand.append(c)
        else:
            self.__players[1].attack_hand.append(c)

    def last_inl(self, message: str, p: player.Player):
        players = self.players()
        if players[0].puid() == p.puid():
            self.__players[0].last_inline_card = message
        else:
            self.__players[1].last_inline_card = message


    def number_of_beaten(self, num: int, p: player.Player):
        players = self.players()
        if players[0].puid() == p.puid():
            self.__players[0].number_of_beaten_cards = int
        else:
            self.__players[1].number_of_beaten_cards = int

    def remove(self, c: card.Card, p: player.Player):
        players = self.players()
        if players[0].puid() == p.puid():
            self.__players[0].remove_card(c)
        else:
            self.__players[1].remove_card(c)

    def change_attack_hand(self, lst, p):
        players = self.players()
        if players[0].puid() == p.puid():
            self.__players[0].attack_hand = lst
        else:
            self.__players[1].attack_hand = lst

    def deck(self):
        return self.__deck

    def players(self):
        return self.__players

    def initialize_game(self):
        deck = generate_deck()
        random.seed()  # TODO: 42 для тестирования
        random.shuffle(deck)
        tmp = deck.pop()
        self.trump = tmp.suit
        self.__players[0].set_cards(deck[-6:])
        self.__players[1].set_cards(deck[-12:-6])
        del deck[-12:]

        min_trump = 15
        for c in self.__players[0].cards():
            if c.suit == self.trump and c.value < min_trump:
                min_trump = c.value
                self.start_player = self.__players[0]
        for c in self.__players[1].cards():
            if c.suit == self.trump and c.value < min_trump:
                min_trump = c.value
                self.start_player = self.__players[1]

        deck.insert(0, tmp)
        self.__deck = deck
        return self

    def field_view_for_player(self, me: player.Player, turn: player.Player):  # turn - чей ход, me - кто спрашивает
        if self.__players[0].puid() == me.puid():
            query_player = self.__players[0]
            enemy_player = self.__players[1]
        elif self.__players[1].puid() == me.puid():
            query_player = self.__players[1]
            enemy_player = self.__players[0]
        else:
            raise ValueError('Wrong player-ID')

        table_to_print = ""

        for e in self.table:
            att_c = e
            def_c = self.table[e]
            if def_c != card.NONECARD:
                table_to_print += cards_to_str([att_c]) + '|' + cards_to_str([def_c]) + '  '
            else:
                table_to_print += cards_to_str([att_c]) + '  '

        if me.puid() != turn.puid():
            message_text = "Игроки:\n" \
                           "{0}  {1}\n" \
                           "{2}  {3}\n" \
                           "\nКозырь {7}"\
                           "\nКолода 🃏x{4} \n" \
                           "\nСтол: {5}\n\n" \
                           "Ходит {6}".format(enemy_player.name, '🃏' * enemy_player.cards_quantity(),
                                              query_player.name,
                                              cards_to_str(query_player.cards()), len(self.__deck),
                                              table_to_print, turn.name, suit_to_emoji[self.trump.name])
        else:
            message_text = "Игроки:\n" \
                           "{0}  {1}\n" \
                           "{2}  {3}\n" \
                           "\nКозырь {7}" \
                           "\nКолода 🃏x{4} \n" \
                           "\nСтол: {5}\n\n" \
                           "Ваш ход!".format(enemy_player.name, '🃏' * enemy_player.cards_quantity(), query_player.name,
                                             cards_to_str(query_player.cards()), len(self.__deck),
                                             table_to_print, turn.name, suit_to_emoji[self.trump.name])
        return message_text
