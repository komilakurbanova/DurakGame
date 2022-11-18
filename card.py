import enum
from enum import Enum


class Card(object):
    class Suit(Enum):
        SPADES = 'S'  # ♤
        CLUBS = 'C'  # ♧
        DIAMONDS = 'D'  # ♢
        HEARTS = 'H'  # ♡

    #class Value(enum.IntEnum):
    #    SIX = 6
    #    SEVEN = 7
    #    EIGHT = 8
    #    NINE = 9
    #    TEN = 10
    #    J = 11
    #    Q = 12
    #    K = 13
    #    A = 14

    def __init__(self,  *args):
        try:
            if len(args) == 2:
                value = int(args[0])
                suit = Card.Suit(args[1])
            elif len(args) == 1:
                str = args[0]
                value = int(str[:-1])
                suit = Card.Suit(str[-1])
            else:
                raise ValueError('Incorrect card arguments number')
        except ValueError:
            raise ValueError('Incorrect card')
        self.value = value
        self.suit = suit

    def value_str(self):
        extra = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        if 10 < self.value < 15:
            return extra[self.value]
        else:
            return str(self.value)

    def __str__(self):
        return "{0}-{1}".format(self.value_str(), self.suit.name)

    def __lt__(self, other):  # p1.__lt__(p2)  <=> p1 < p2
        if self.suit != other.suit:
            return False
        return self.value < other.value

    def __gt__(self, other):  # p1.__gt__(p2)  <=> p1 > p2
        if self.suit != other.suit:
            return False
        return self.value > other.value

    def __eq__(self, other):
        return other.value == self.value and other.suit == self.suit

    def __ne__(self, other):
        return not self == other
