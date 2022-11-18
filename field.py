import card
import player
from typing import List
import random


def generate_deck():
    sample_deck = [card.Card(val, suit) for val in range(6, 15) for suit in card.Card.Suit]
    return sample_deck


class Field(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.__players = [p1, p2]
        self.__deck = []
        self.trump = None
        self.__table = []
        self.start_player = None

    def initialize_game(self):
        deck = generate_deck()
        random.seed(42)  # надо бы улучшить рандом, но пока и так сойдет
        random.shuffle(deck)
        print_cards(deck)
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


def print_cards(x: List[card.Card]):  # это просто для тестирования удобная вещь
    for c in x:
        print(c, end=' ')
    print()


