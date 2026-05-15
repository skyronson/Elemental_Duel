import random
from itertools import product
from colorama import Fore
from utils.data_loader import load_elements

def heal(target, value):
    if target.hp + value >= target.max_hp:
        target.hp = target.max_hp
    else:
        target.hp += value

def get_color(card):
    colors = load_elements()["colors"]
    for elem, col in colors.items():
        if elem in card:
            if isinstance(col, list):
                r, g, b = col
                return f'\033[38;2;{r};{g};{b}m'
            else:
                return getattr(Fore, col.upper())
    if "???" in card:
        return ""
    return ""

def parse_effect(effect_str):
    parts = effect_str.split()
    name = parts[0]
    if len(parts) >= 2:
        lvl = int(parts[1])
    else:
        lvl = 0
    return name, lvl

def is_hand_full(player):
    hand = player.hand
    limit = player.max_cards
    if len(hand) >= limit:
        print(f"\nКОЛИЧЕСТВО КАРТ В РУКЕ НЕ МОЖЕТ БЫТЬ БОЛЬШЕ {limit}!")
        return True
    else:
        return False