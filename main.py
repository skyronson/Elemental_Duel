from game.engine import GameEngine
from game.player import Player
from game.deck import Deck
from utils.data_loader import load_combinations, load_elements, load_roman

def main():
    combos = load_combinations()
    elems = load_elements()
    roman = load_roman()

    # Создание колоды
    deck_obj = Deck()
    deck_obj.create_deck()

    # Создание игроков
    p1 = Player()
    p2 = Player()
    p1.opponent = p2
    p2.opponent = p1
    p1.set_name()
    p2.set_name()

    # Раздача стартовых карт
    for _ in range(8):
        p1.hand.append(deck_obj.deck.pop())
        p2.hand.append(deck_obj.deck.pop())
    p1.hand.extend(["ВОДА 10", "ЗЕМЛЯ 10", "ВОЗДУХ 10", "ЗЕМЛЯ 10", "ОГОНЬ 10"])
    for _ in range(2):
        p2.hand.append(deck_obj.deck.pop())

    engine = GameEngine(p1, p2, deck_obj, combos, roman, elems["colors"])
    engine.run()

if __name__ == "__main__":
    main()
