from typing import List
import card

CARDS_FOR_PLAYER = 6


class Player(object):
    def __init__(self, puid: str, name: str, cards: List[card.Card], last_inline_card="", name_anon="Анон"):
        self.__puid = puid
        self.username = name
        self.__cards = cards
        self.active = False
        self.defensive = False
        self.name = name_anon
        self.last_inline_card = last_inline_card
        self.attack_hand: List[card.Card] = []
        self.number_of_beaten_cards = 0

    def set_cards(self, cards: List[card.Card]):  # присвоить игроку эти карты
        self.__cards = cards

    def cards_quantity(self):  # число карт у игрока
        return len(self.__cards)

    def puid(self):
        return self.__puid

    def cards(self):
        return self.__cards

    def add_attack_card(self, c: card.Card):
        self.attack_hand.append(c)

    def __add_cards_from_deck(self, deck: List[card.Card], ind: int):  # взять ind карт из колоды
        print(ind)
        print(len(deck))
        print(deck)
        self.__cards += deck[:ind]
        del deck[:ind]

    def take_cards_from_field(self, cards):  # брать со стола (пас или что-то такое)
        for c in cards:
            if c != card.NONECARD:
                self.__cards.append(c)

    def take_lack_cards_from_deck(self, deck: List[card.Card]):  # брать из колоды недостающие
        lack = max(0, CARDS_FOR_PLAYER - self.cards_quantity())
        to = min(lack, len(deck))
        self.__add_cards_from_deck(deck, to)

    def remove_card(self, c: card.Card):
        self.__cards.remove(c)


def sort_cards(cards: List[card.Card]):
    return sorted(cards)
