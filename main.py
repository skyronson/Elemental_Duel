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
    cards_1 = deck_obj.draw_cards(6, player=p1)
    p1.hand.extend(cards_1)
    p1.hand.extend(['ОГОНЬ 10', 'ВОДА 10', 'ВОЗДУХ 10', 'ОГОНЬ 10', 'ВОДА 10', 'ВОЗДУХ 10'])
    cards_2 = deck_obj.draw_cards(10, player=p2)
    p2.hand.extend(cards_2)


    engine = GameEngine(p1, p2, deck_obj, combos, roman, elems["colors"])
    engine.run()

if __name__ == "__main__":
    main()