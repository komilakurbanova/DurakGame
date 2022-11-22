import card
import player
from typing import List
import random


def generate_deck():
    sample_deck = [card.Card(val, suit) for val in range(6, 15) for suit in card.Card.Suit]
    return sample_deck


def cards_to_list(cards: List[card.Card]):
    suit_to_emoji = {'SPADES': '♠', 'CLUBS': '♣', 'DIAMONDS': '♦', 'HEARTS': '♥'}
    ret = ""
    for c in cards:
        ret += ("{0}{1}".format(c.value_str(), suit_to_emoji[c.suit.name])) + ' '
    return ret


class Field(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.__players = [p1, p2]
        self.__deck = []
        self.trump = None
        self.table = []
        self.start_player = None

    def deck(self):
        return self.__deck

    def players(self):
        return self.__players

    def initialize_game(self):
        deck = generate_deck()
        random.seed()  # надо бы улучшить рандом, но пока и так сойдет
        random.shuffle(deck)
        # print_cards(deck)
        self.trump = deck.pop().suit
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

        deck.insert(0, self.trump)
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
        if me.puid() != turn.puid():
            message_text = "Игроки:\n" \
                           "{0}  {1}\n" \
                           "{2}  {3}\n" \
                           "\nКолода 🃏x{4} \n" \
                           "\nСтол: {5}\n\n" \
                           "Ходит {6}".format(enemy_player.name, '🃏' * enemy_player.cards_quantity(),
                                              query_player.name,
                                              cards_to_list(query_player.cards()), len(self.__deck),
                                              cards_to_list(self.table), turn.name)
        else:
            message_text = "Игроки:\n" \
                           "{0}  {1}\n" \
                           "{2}  {3}\n" \
                           "\nКолода ?x{4} \n" \
                           "\nСтол: {5}\n\n" \
                           "Ваш ход!".format(enemy_player.name, '?' * enemy_player.cards_quantity(), query_player.name,
                                             cards_to_list(query_player.cards()), len(self.__deck),
                                             cards_to_list(self.table))
        return message_text


def print_cards(x: List[card.Card]):  # это просто для тестирования удобная вещь
    for c in x:
        print(c, end=' ')
    print()


#p1 = player.Player('1', 'first', [])
#p2 = player.Player('2', 'second', [])
#f = Field(p1, p2)
#f.initialize_game()
#print(f.field_view_for_player(p2, p1))
