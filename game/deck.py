import random
from itertools import product
from utils.helpers import is_hand_full

class Deck:
    def __init__(self):
        self.deck = None
        self.elements = ["ОГОНЬ", "ВОДА", "ЗЕМЛЯ", "ВОЗДУХ"] * 2
        self.numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

    def create_deck(self):
        deck = list(product(self.elements, self.numbers))
        deck = [" ".join(card) for card in deck]
        random.shuffle(deck)
        self.deck = deck

    # Функция для безопасного взятия карт из колоды
    def draw_cards(self, count, player=None):
        drawn = []
        new = 0
        for i in range(count):
            if len(self.deck) == 0:
                self.refill_deck()  # Перезаполняем колоду если она пустая
            if len(self.deck) > 0:
                if player and not is_hand_full(player.hand + [1 for _ in range(new)]):
                    drawn.append(self.deck.pop())
                    new += 1
                else:
                    break
        return drawn

    # Функция для обновления колоды карт, когда они заканчиваются
    def refill_deck(self):
        self.create_deck()
        print("\nКОЛОДА ОБНОВЛЕНА")