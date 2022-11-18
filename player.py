from typing import List
import card

CARDS_FOR_PLAYER = 6


class Player(object):
    def __init__(self, puid: str, cards: List[card.Card]):
        self._puid = puid
        self._cards = cards

    def cards_quantity(self):
        return len(self._cards)

    def puid(self):
        return self._puid

    def cards(self):
        return self._cards

    def __add_cards_from_deck(self, deck: List[card.Card], ind: int):
        self._cards += deck[:ind]
        del deck[:ind]

    def take_cards_from_field(self, cards: List[card.Card]):  # брать со стола
        self._cards += cards

    def take_lack_cards_from_deck(self, deck: List[card.Card]):  # брать из колоды
        lack = max(0, CARDS_FOR_PLAYER - self.cards_quantity())
        to = min(lack, len(deck))
        self.__add_cards_from_deck(deck, to)

    def remove_card(self, c: card.Card):
        self._cards.remove(c)

    def sort_cards(self):  # возвращает словарь отсорченных по мастям карт (для реализации игры с ботом полезно)
        cards_by_suits = {}
        for s in card.Card.Suit:
            cards_by_suits[s] = []
        for c in self._cards:
            cards_by_suits[c.suit].append(c.value)
        for s in card.Card.Suit:
            cards_by_suits[s].sort()
        return cards_by_suits



