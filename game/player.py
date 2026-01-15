import itertools as it
import functools
import math
import pandas as pd
import json
import ast
import random
import time
from colorama import init, Fore, Back, Style
from ui.display import show_combat_message, show_player_state, show_new_cards_message, show_end_game_message
from utils.data_loader import load_elements, load_combinations, load_roman
from utils.helpers import heal, get_color


colors = load_elements()['colors']
roman = load_roman()
combinations = load_combinations()
init(autoreset=True)
italic = '\033[3m'
reset = '\033[0;0m'


class Player:
    def __init__(self):
        self.name = ''                                   # Имя игрока
        self.hand = []                                   # Карты в руке
        self.max_hp = 50                                 # Максимальное количество здоровья
        self.hp = 50                                     # Текущее количество здоровья
        self.power_coeff = 1                             # Множитель силы, снижается эффектом «ИСТОЩЕНИЕ»
        self.status_effects = []                         # Эффекты, наложенные на игрока
        self.status_effects_bar = set()                  # Шкала имеющихся эффектов
        self.last_move = []                              # Последний ход игрока
        self.last_effect = ""                            # Последний наложенный на игрока эффект
        self.is_shell_shocked = False                    # Статус эффекта «КОНТУЗИЯ»
        self.spells_counter = 0                          # Счётчик успешно применённых заклинаний
        self.opponent = None


    def set_name(self):
        name = input("Введите имя игрока: ")
        if name.strip():
            self.name = name
        else:
            if not self.opponent.name:
                self.name = "Игрок_1"
            else:
                self.name = "Игрок_2"



    def update_status(self, is_defended, deck, moves_counter):
        skip_turn = False
        game_over = False

        print("\n")

        names_of_effects = list(map(lambda x: x.split()[0], self.status_effects))

        if "БАРЬЕР" in names_of_effects:
            idx = names_of_effects.index("БАРЬЕР")
            self.status_effects.pop(idx)

        for effect in self.opponent.status_effects:
            if "БАРЬЕР" in effect:
                lvl = int(effect.split()[1])
                print(f"В этом ходу урон от ваших карт снижен на {italic}{lvl} ед.")

        if "ЦИКЛОН" in names_of_effects:
            cyclone_rgb = '\033[38;2;255;255;255m'
            idx = names_of_effects.index("ЦИКЛОН")
            effect = self.status_effects[idx]
            duration = int(effect.split()[1])

            if duration == 0:
                print(f"\n{Style.BRIGHT}{cyclone_rgb}«ЦИКЛОН»{reset} прекратил своё существование")
                self.status_effects.remove(effect)
            else:
                spells = ["ЦУНАМИ", "ГЕЙЗЕР", "МОЛНИЯ"]
                lvls = [0, 1, 2, 3]
                RGBs = {
                    "ЦУНАМИ": '\033[38;2;72;89;240m',
                    "ГЕЙЗЕР": '\033[38;2;204;229;255m',
                    "МОЛНИЯ": '\033[38;2;230;210;20m'
                }
                spell = random.choice(spells)
                lvl = random.choice(lvls + ([4, 5] if spell == "ГЕЙЗЕР" else []))

                case = "ход" if duration == 1 else "хода"
                print(f"{Style.BRIGHT}{cyclone_rgb}«ЦИКЛОН»{reset} вызвал заклинание {Style.BRIGHT}{RGBs[spell]}«{spell} {roman[str(lvl)]}»{reset}. Осталось: {italic}{duration} {case}")

                if spell == "ГЕЙЗЕР":
                    self.opponent.cast_spell(spell, lvl * 4, cyclone=True)
                else:
                    self.opponent.cast_spell(spell, lvl * 7, cyclone=True)
                idx = self.status_effects.index(effect)
                self.status_effects[idx] = f"ЦИКЛОН {duration - 1}"

        if self.hp <= 0:
            return {"skip_turn": False, "game_over": True}

        for effect in self.status_effects.copy():  # Делаем копию списка для итерации

            if "ГОРЕНИЕ" in effect:
                if self.last_effect in effect and is_defended:
                    self.status_effects.remove(effect)
                    print("Эффект «ГОРЕНИЕ» не был применен")
                else:
                    duration = int(effect.split()[1])
                    if duration > 1:
                        self.hp -= 4
                        case = 'хода' if (duration - 1) >= 2 else 'ход'
                        print(f"Вы получаете {italic}4 ед. урона{reset} от эффекта «ГОРЕНИЕ». Осталось: {italic}{duration - 1} {case}")
                        idx = self.status_effects.index(effect)
                        self.status_effects[idx] = f"ГОРЕНИЕ {duration - 1}"  # Обновляем эффект в списке
                    else:
                        self.hp -= 4
                        print(f"Вы получаете {italic}4 ед. урона{reset} от эффекта «ГОРЕНИЕ» (последний ход)")
                        self.status_effects.remove(effect)  # Удаляем эффект


            if "ГРЯЗНУЛЯ" in effect:
                if self.last_effect in effect and is_defended:
                    self.status_effects.remove(effect)
                    print("Эффект «ГРЯЗНУЛЯ» не был применен")
                else:
                    lvl = int(effect.split()[1])
                    available_cards = list(filter(lambda x: "???" not in x, self.hand.copy()))
                    for i in range(lvl):
                        if available_cards == []:
                            break
                        card = random.choice(available_cards)
                        card_indx = self.hand.index(card)
                        card_lvl = int(card.split()[1])
                        dirt = f'ГРЯЗЬ {max(1, card_lvl // 2)}'
                        self.hand[card_indx] = dirt
                        available_cards.remove(card)
                    self.status_effects.remove(effect)


            if "СЛЕПОТА" in effect:
                if self.last_effect in effect and is_defended and effect.split()[2] != "0":
                    self.status_effects.remove(effect)
                    print("Эффект «СЛЕПОТА» не был применен")
                else:
                    lvl = int(effect.split()[1])
                    duration = int(effect.split()[2])
                    fogged_cards = ast.literal_eval(effect.split('fc')[1])
                    available_cards = [c for c in self.hand if c != '   ???   ']

                    if duration == 0:
                        for i, card in enumerate(self.hand):
                            if card == '   ???   ' and fogged_cards:
                                self.hand[i] = fogged_cards.pop(0)
                        self.status_effects.remove(effect)

                    else:
                        for i in range(lvl):
                            if available_cards == []:
                                break
                            card = random.choice(available_cards)
                            idx = self.hand.index(card)
                            self.hand[idx] = '   ???   '
                            available_cards.remove(card)
                            fogged_cards.append(card)

                        case = 'ходов' if duration >= 2 else 'хода'
                        print(f"Вы перестаёте видеть {italic}{lvl} шт. карт{reset} в руке из-за эффекта «СЛЕПОТА» и не можете их использовать в течение {italic}{duration} {case}")
                        idx = self.status_effects.index(effect)
                        self.status_effects[idx] = f"СЛЕПОТА {lvl} {duration - 1} fc{fogged_cards}"


            if "ОБЕЗОРУЖИВАНИЕ" in effect:
                if self.last_effect in effect and is_defended:
                    self.status_effects.remove(effect)
                    print("Эффект «ОБЕЗОРУЖИВАНИЕ» не был применен")
                else:
                    lvl = int(effect.split()[1])
                    if lvl >= len(self.hand):
                        self.hand = []
                    else:
                        removed_cards = random.sample(list(range(len(self.hand))), lvl)
                        left_cards = list(filter(lambda x: x not in removed_cards, list(range(len(self.hand)))))
                        self.hand = [self.hand[i] for i in left_cards]
                    print(f"Вы сбрасываете {italic}{lvl} шт. карт")
                    self.status_effects.remove(effect)


            if "МОЛНИЯ" in effect:
                rgb = '\033[38;2;230;210;20m'
                if (self.last_effect in effect and is_defended) or effect == 'МОЛНИЯ 0':
                    self.status_effects.remove(effect)
                    print(f"Эффект заклинания {Style.BRIGHT}{rgb}«МОЛНИЯ»{reset} не был применен")
                else:
                    lvl = int(effect.split()[1])
                    if len(self.hand) != 0:
                        card = sorted(self.hand, key=lambda x: -int(x.split()[1]))[0]
                        color = get_color(card)
                        magic_dmg = math.ceil(int(card.split()[1]) * (lvl / 2))
                        self.hand.remove(card)
                        self.hp -= magic_dmg
                        self.status_effects.remove(effect)
                        print(f"Вы сбрасываете карту {color}«{card}»{reset} и получаете {italic}{magic_dmg} ед. урона")


            if "ЗАВАЛ" in effect:
                if self.last_effect in effect and is_defended:
                    exhaustion = float(effect.split()[1])
                    duration = int(effect.split()[2])
                    self.power_coeff = 1 - exhaustion
                    case = "ход" if duration == 1 else "хода"
                    print(f"В этом ходу ваши заклинания на {italic}{round(exhaustion * 100)}%{reset} слабее. Осталось: {italic}{duration} {case}")
                    self.status_effects.append(f"ИСТОЩЕНИЕ {duration - 1}")
                    self.status_effects.remove(effect)
                else:
                    skip_turn = True
                    self.last_move.clear()
                    print("ВЫ ПРОПУСКАЕТЕ ХОД, ПОТОМУ ЧТО ПОПАЛИ В ЗАВАЛ")
                    self.status_effects.remove(effect)
                    time.sleep(2)
                    break


            if "ИСТОЩЕНИЕ" in effect:
                if self.last_effect in effect and is_defended:
                    self.power_coeff = 1
                    self.status_effects.remove(effect)
                    print("Эффект «ИСТОЩЕНИЕ» не был применен")
                else:
                    duration = int(effect.split()[1])
                    if duration == 0:
                        self.power_coeff = 1
                        self.status_effects.remove(effect)
                    else:
                        case = "ход" if duration == 1 else "хода"
                        print(f"В этом ходу ваши заклинания на {italic}{int((1 - self.power_coeff) * 100)}%{reset} слабее. Осталось: {italic}{duration} {case}")
                        idx = self.status_effects.index(effect)
                        self.status_effects[idx] = f"ИСТОЩЕНИЕ {duration - 1}"


            if "НАПАЛМ" in effect:
                if self.last_effect in effect and is_defended:
                    duration = int(effect.split()[2])
                    case = "ход" if duration == 1 else "хода"
                    print(f"В этом ходу негативные эффекты ваших заклинаний с вероятностью в 50% могут также примениться на вас. Осталось: {italic}{duration} {case}")
                    self.is_shell_shocked = True
                    self.status_effects.append(f"КОНТУЗИЯ {duration - 1}")
                    self.status_effects.remove(effect)

                else:
                    lvl = int(effect.split()[1])
                    rgb = '\033[38;2;255;126;0m'
                    magic_dmg = (len(list(filter(lambda x: "ОГОНЬ" in x, self.opponent.hand))) + 1) * (lvl + 2)
                    self.hp -= magic_dmg
                    print(f"{Style.BRIGHT}{rgb}«НАПАЛМ»{reset} наносит {italic}{magic_dmg} ед. урона")
                    self.status_effects.remove(effect)


            if "ЗЕМЛЕТРЯСЕНИЕ" in effect:
                lvl = int(effect.split()[1])
                if self.last_effect in effect and is_defended:
                    corrosion = math.ceil(lvl / 2)
                    for i in range(len(self.hand)):
                        try:
                            card = self.hand[i]
                            if card != '   ???   ':
                                element, power = card.split()
                                new_power = max(1, int(power) - corrosion)
                                self.hand[i] = f"{element} {new_power}"
                        except (ValueError, IndexError) as e:
                            print(e)
                            continue
                    print(f"Ваши карты теряют {italic}{corrosion} ед. силы")
                else:
                    self.hand = list(filter(lambda x: int(x.split()[1]) > (lvl + 1), self.hand))
                    print(f"Вы сбрасываете все карты {italic}силы {lvl + 1}{reset} или меньше")
                    self.status_effects.remove(effect)


            if "КОНТУЗИЯ" in effect:
                duration = int(effect.split()[1])
                if duration == 0:
                    self.is_shell_shocked = False
                    self.status_effects.remove(effect)
                else:
                    case = "ход" if duration == 1 else "хода"
                    print(f"В этом ходу негативные эффекты ваших заклинаний с вероятностью в 50% могут также примениться на вас. Осталось: {italic}{duration} {case}")
                    self.is_shell_shocked = True
                    idx = self.status_effects.index(effect)
                    self.status_effects[idx] = f"КОНТУЗИЯ {duration - 1}"


        if self.hp <= 0:
            game_over = True

        names_of_effects = list(map(lambda x: x.split()[0], self.status_effects))

        if moves_counter > 2 and moves_counter % 10 != 0 and moves_counter % 10 != 1 and "ЗАВАЛ" not in names_of_effects:
            new_cards = deck.draw_cards(2, player=self)
            self.hand.extend(new_cards)
            show_new_cards_message(new_cards)

        elif moves_counter % 10 == 0:
            # Игрок берет карты
            new_cards = deck.draw_cards(10, player=self)
            self.hand.extend(new_cards)
            # Противник тоже берет карты
            opponent_cards = deck.draw_cards(10, player=self.opponent)
            self.opponent.hand.extend(opponent_cards)
            show_new_cards_message(new_cards)

        return {
            "skip_turn": skip_turn,
            "game_over": game_over,
            # можно добавить другие флаги: heal_amount, draw_cards и т.д.
        }


    def make_move(self, nums, deck, moves_counter):
        nums = nums.split()
        cards = []
        for num in nums:
            cards.append(self.hand[int(num) - 1])

        if len(set(nums)) != len(nums):
            print("\nОШИБКА! ВЫ ВЫБРАЛИ ОДНУ КАРТУ НЕСКОЛЬКО РАЗ")
            return False

        if '   ???   ' in cards:
            print("\nВЫ НЕ МОЖЕТЕ ВЫБРАТЬ ЗАТУМАНЕННЫЕ КАРТЫ")
            return False

        if (all(map(lambda i: i.split(" ")[0] == cards[0].split(" ")[0], cards)) and len(cards) == 2) or\
            (all(map(lambda i: i.split(" ")[1] == cards[0].split(" ")[1], cards)) and len(cards) <= 4):
            print("\nВАШ ХОД: ")
            print("{:-^320}".format(""))

            for i, card in enumerate(cards[:]):
                self.hand.remove(card)
                color = get_color(card)
                if i != len(cards) - 1:
                    print(color + card, end=' + ')
                else:
                    print(color + card)

            dmg = functools.reduce(lambda x, y: x + y, map(lambda i: int(i.split()[1]), cards))
            pure_dmg = dmg

            for effect in self.opponent.status_effects:
                if "БАРЬЕР" in effect:
                    lvl = int(effect.split()[1])
                    if pure_dmg >= lvl:
                        pure_dmg -= lvl * len(cards)
                    else:
                        pure_dmg = 0
                    for i, card in enumerate(cards):
                        element, power = card.split()
                        power = max(0, int(power) - lvl)
                        cards[i] = f"{element} {power}"
                    self.opponent.status_effects.remove(effect)

            self.last_move = cards
            self.opponent.hp -= pure_dmg
            print(f'Вы нанесли противнику {italic}{pure_dmg} ед. урона')

            played_combination = sorted(list(map(lambda i: i.split()[0], cards)))
            if played_combination in combinations.values():
                for spell in combinations.keys():
                    if combinations[spell] == played_combination:
                        self.cast_spell(spell, dmg, deck, moves_counter)

            print("{:-^320}".format(""))
            return True

        else:
            print("\nВЫБРАНА НЕВЕРНАЯ КОМБИНАЦИЯ")
            return False



    def defend(self, moves_counter):
        if len(self.opponent.last_move) == 0:
            return

        print("\nПРЕДЫДУЩИЙ ХОД ПРОТИВНИКА: ", end=' ')
        for i, card in enumerate(self.opponent.last_move[:]):
            color = get_color(card)
            if i != len(self.opponent.last_move) - 1:
                print(color + card, end=' + ')
            else:
                print(color + card, end='')
        print()
        show_player_state(self, moves_counter)

        while True:
            nums = input("\nВЫБЕРИТЕ КАРТЫ, ЧТОБЫ ЗАЩИТИТЬСЯ:\n").strip()
            if nums == '':
                continue

            elif nums == '0':
                print("\nВЫ НЕ СТАЛИ ЗАЩИЩАТЬСЯ")
                last_move = list(map(lambda x: x.split()[0], self.opponent.last_move))
                show_combat_message(self.opponent, last_move)
                time.sleep(2)
                return False

            elif all(map(lambda i: i.isdigit(), nums.split())) and len(self.opponent.last_move) == len(nums.split()):

                def collide(att_card, def_card):
                    if att_card.split()[0] == "ВОДА":
                        if def_card.split()[0] == "ВОЗДУХ":
                            def_card_lvl = int(def_card.split()[1]) * 2
                        elif def_card.split()[0] == "ЗЕМЛЯ":
                            def_card_lvl = int(def_card.split()[1]) // 2
                        elif def_card.split()[0] == "ОГОНЬ":
                            def_card_lvl = int(def_card.split()[1])
                        elif def_card.split()[0] == "ГРЯЗЬ":
                            def_card_lvl = int(def_card.split()[1])
                        else:
                            print("\nНЕЛЬЗЯ ЗАЩИЩАТЬСЯ СТИХИЕЙ, КОТОРОЙ ВАС АТАКУЮТ!")
                            return "error"

                    elif att_card.split()[0] == "ВОЗДУХ":
                        if def_card.split()[0] == "ВОДА":
                            def_card_lvl = int(def_card.split()[1]) // 2
                        elif def_card.split()[0] == "ЗЕМЛЯ":
                            def_card_lvl = int(def_card.split()[1])
                        elif def_card.split()[0] == "ОГОНЬ":
                            def_card_lvl = int(def_card.split()[1]) * 2
                        elif def_card.split()[0] == "ГРЯЗЬ":
                            def_card_lvl = int(def_card.split()[1])
                        else:
                            print("\nНЕЛЬЗЯ ЗАЩИЩАТЬСЯ СТИХИЕЙ, КОТОРОЙ ВАС АТАКУЮТ!")
                            return "error"

                    elif att_card.split()[0] == "ЗЕМЛЯ":
                        if def_card.split()[0] == "ВОДА":
                            def_card_lvl = int(def_card.split()[1]) * 2
                        elif def_card.split()[0] == "ВОЗДУХ":
                            def_card_lvl = int(def_card.split()[1])
                        elif def_card.split()[0] == "ОГОНЬ":
                            def_card_lvl = int(def_card.split()[1]) // 2
                        elif def_card.split()[0] == "ГРЯЗЬ":
                            def_card_lvl = int(def_card.split()[1])
                        else:
                            print("\nНЕЛЬЗЯ ЗАЩИЩАТЬСЯ СТИХИЕЙ, КОТОРОЙ ВАС АТАКУЮТ!")
                            return "error"

                    elif att_card.split()[0] == "ОГОНЬ":
                        if def_card.split()[0] == "ВОДА":
                            def_card_lvl = int(def_card.split()[1])
                        elif def_card.split()[0] == "ВОЗДУХ":
                            def_card_lvl = int(def_card.split()[1]) // 2
                        elif def_card.split()[0] == "ЗЕМЛЯ":
                            def_card_lvl = int(def_card.split()[1]) * 2
                        elif def_card.split()[0] == "ГРЯЗЬ":
                            def_card_lvl = int(def_card.split()[1])
                        else:
                            print("\nНЕЛЬЗЯ ЗАЩИЩАТЬСЯ СТИХИЕЙ, КОТОРОЙ ВАС АТАКУЮТ")
                            return "error"

                    elif att_card.split()[0] == "ГРЯЗЬ":
                        def_card_lvl = int(def_card.split()[1])

                    att_card_lvl = int(att_card.split()[1])
                    if att_card_lvl <= def_card_lvl:
                        return att_card_lvl
                    else:
                        return def_card_lvl

                try:
                    flag = False
                    total_dmg = sum(int(card.split()[1]) for card in self.opponent.last_move)  # Общий урон атаки
                    parried_dmg = 0  # Отражённый урон
                    nums = nums.split()
                    cards = []

                    # Сначала получаем карты, но не удаляем их из руки
                    for num in nums:
                        cards.append(self.hand[int(num) - 1])

                    if '   ???   ' in cards:
                        print("\nВЫ НЕ МОЖЕТЕ ВЫБРАТЬ ЗАТУМАНЕННЫЕ КАРТЫ")
                        continue

                    for card_num in range(len(cards)):
                        result = collide(self.opponent.last_move[card_num], cards[card_num])
                        if result == "error":
                            flag = True
                            break
                        parried_dmg += result

                    if flag:
                        print("НЕВЕРНАЯ ЗАЩИТА, ПОПРОБУЙТЕ СНОВА")
                        continue  # Карты не удаляются, цикл начинается заново

                    # Если ошибок нет — удаляем карты из руки и применяем урон
                    for card in cards:
                        self.hand.remove(card)

                    self.hp += parried_dmg  # Увеличиваем HP на отражённый урон

                    if parried_dmg == total_dmg:
                        print("\nВЫ УСПЕШНО ОТРАЗИЛИ АТАКУ ПРОТИВНИКА")
                        # Шуточное сообщение при успешной защите
                        defense_messages = [
                            "🎯 Броня выдержала! Вы как танк!",
                            "🎯 Защита сработала - противник в ярости!",
                            "🎯 Вы отбили атаку как настоящий джедай!",
                            "🎯 Противник в шоке от вашей защиты!",
                            "🎯 Вы сделали это красиво, как в кино!",
                            "🎯 Вы дали джазу противнику"
                        ]
                        print(f"{Fore.CYAN}{random.choice(defense_messages)}{reset}")
                        time.sleep(2)
                        return True
                    else:
                        print(f"\nВЫ НЕУДАЧНО ОТРАЗИЛИ АТАКУ, ИТОГО ПОТЕРЯВ {italic}{abs(total_dmg - parried_dmg)} ед. здоровья")
                        last_move = list(map(lambda x: x.split()[0], self.opponent.last_move))
                        self.opponent.spells_counter += 1
                        # Шуточное сообщение при неудачной защите
                        show_combat_message(self.opponent, last_move)
                        time.sleep(2)
                        return False

                except IndexError:
                    print(f"\nВЫБРАНЫ НЕВЕРНЫЕ КАРТЫ")
                    continue

            else:
                print("\nОШИБКА ВВОДА!")
                continue



    def cast_spell(self, spell, dmg, deck, moves_counter, cyclone=False):

        # ОРДИНАРНЫЕ КОМБИНАЦИИ

        if spell == 'ЛЕЧЕНИЕ':
            lvl = round(((dmg - 1) // 4 + 1) * self.power_coeff)
            heal(self, lvl)
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;255;255;188m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"Вы восстанавливаете себе {italic}{lvl} ед. здоровья")


        elif spell == 'ТЕЛЕКИНЕЗ':
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            new_cards = deck.draw_cards(lvl, player=self)
            self.hand.extend(new_cards)
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;229;204;255m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"Вы берете {italic}{lvl} шт. карт")


        elif spell == 'БАРЬЕР':
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            self.status_effects.append(f"БАРЬЕР {lvl}")
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;144;165;39m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"Урон карт противника от атак снижается на {italic}{lvl} ед. на следующем ходу")


        elif spell == "ОГНЕННЫЙ ШАР":
            lvl = round(((dmg - 1) // 4 + 1) * self.power_coeff)
            self.opponent.hp -= lvl
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;255;199;18m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"Вы наносите противнику {italic}{lvl} ед. урона")


        # РЕДКИЕ КОМБИНАЦИИ

        elif spell == "ЦУНАМИ":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            heads_or_tails = 0
            if self.is_shell_shocked and not cyclone:
                heads_or_tails = random.randint(0, 1)
            if lvl == 1:
                self.opponent.power_coeff = 0.75
                if heads_or_tails: self.power_coeff = 0.75
            elif lvl == 2:
                self.opponent.power_coeff = 0.5
                if heads_or_tails: self.power_coeff = 0.5
            elif lvl == 3:
                self.opponent.power_coeff = 0
                if heads_or_tails: self.power_coeff = 0
            self.opponent.status_effects.append("ИСТОЩЕНИЕ 1")
            if not cyclone:
                self.opponent.last_effect = "ИСТОЩЕНИЕ"

            rgb = '\033[38;2;72;89;240m'

            if not cyclone:
                if lvl != 0:
                    show_player_state(self, moves_counter)
                    print(f"\nВыберите до {italic}{lvl} шт. карт{reset}, которые хотите поменять, или «0» для отмены")

                    while True:
                        try:
                            action = input("\nВВОД:\n").strip()
                            if action == '0':
                                print("\nВЫ НЕ СТАЛИ МЕНЯТЬ КАРТЫ\n")
                                break

                            chosen_nums = list(map(int, action.split()))
                            length = len(chosen_nums)

                            if length > lvl:
                                print("\nВЫБРАНО СЛИШКОМ МНОГО КАРТ")
                                continue

                            # Проверяем корректность номеров карт
                            if not all(map(lambda x: 1 <= x <= len(self.hand), chosen_nums)):
                                print(f"\nНЕВЕРНЫЙ НОМЕР КАРТЫ! Выберите от 1 до {len(self.hand)}")
                                continue

                            # Проверяем, что выбраны не туманенные карты
                            chosen_cards = []
                            has_fogged = False

                            for num in chosen_nums:
                                idx = num - 1
                                card = self.hand[idx]
                                if card == '   ???   ':
                                    has_fogged = True
                                    break
                                chosen_cards.append(card)

                            if has_fogged:
                                print("\nВЫ НЕ МОЖЕТЕ ВЫБРАТЬ ЗАТУМАНЕННЫЕ КАРТЫ")
                                continue

                            # Если все проверки пройдены - меняем карты
                            for card in chosen_cards:
                                self.hand.remove(card)
                                self.hand.extend(deck.draw_cards(1))

                            print(f"\nПОЛУЧЕНЫ НОВЫЕ КАРТЫ: ", end='')

                            for i, card in enumerate(self.hand[(-length):]):
                                if i != length - 1:
                                    print(get_color(card) + card, end=', ')
                                else:
                                    print(get_color(card) + card, end='\n\n')
                            break  # ← ВАЖНО: ВЫХОДИМ ИЗ ЦИКЛА ПОСЛЕ УСПЕШНОЙ ЗАМЕНЫ

                        except ValueError:
                            print("\nОШИБКА ВВОДА! Введите числа через пробел")
                        except Exception as e:
                            print(f"ОШИБКА! {e}")

                print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Снижает мощность заклинаний противника на {italic}{int((1 - self.opponent.power_coeff) * 100)}%{reset} на следующем ходу")

            if heads_or_tails and not cyclone:
                self.status_effects.append("ИСТОЩЕНИЕ 1")
                print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ГРЯЗЕВОЙ ПОТОП":
            lvl = round(((dmg - 1) // 5 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ГРЯЗНУЛЯ {lvl}")
            self.opponent.last_effect = "ГРЯЗНУЛЯ"
            rgb = '\033[38;2;170;102;0m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ПАССИВНЫЙ ЭФФЕКТ:{reset} Заполняет руку противника {italic}{lvl+1} картами {get_color('ГРЯЗЬ')}ГРЯЗИ")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Заменяет {italic}{lvl} шт. карт{reset} в колоде противника на {italic}{get_color('ГРЯЗЬ')}ГРЯЗЬ{reset} с пониженными вдвое характеристиками")

            dirt_cards = deck.draw_cards(lvl+1, player=self.opponent)
            for i in range(len(dirt_cards)):
                card = dirt_cards[i]
                card_lvl = int(card.split()[1])
                dirt_cards[i] = f'ГРЯЗЬ {max(1, card_lvl // 2)}'
            self.opponent.hand.extend(dirt_cards)

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ГРЯЗНУЛЯ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ГЕЙЗЕР":
            lvl = round(((dmg - 1) // 4 + 1) * self.power_coeff)
            add_power = round(((dmg - 1) // 7 + 1) * self.power_coeff)

            for card in self.hand:
                if card != '   ???   ':
                    element, power = card.split()
                    if element == "ВОЗДУХ":
                        power = min(10, int(power) + add_power)
                        idx = self.hand.index(card)
                        card = f"{element} {power}"
                        self.hand[idx] = card

            self.opponent.status_effects.append(f"СЛЕПОТА {lvl} 1 fc[]")
            RGBs = ['\033[38;2;204;229;255m', '\033[38;2;18;255;167m']

            if not cyclone:
                self.opponent.last_effect = "СЛЕПОТА"
                print(f"Вы применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman[str(lvl)]}»")
                print(f"{Style.BRIGHT}ПАССИВНЫЙ ЭФФЕКТ: {RGBs[1]}«ДЫХАНИЕ ДРАКОНА»{reset}. Все карты {italic}{get_color('ВОЗДУХ')}ВОЗДУХА{reset} в вашей руке получают {italic}+{add_power} к силе")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Накладывает на противника эффект «СЛЕПОТА», из-за чего он перестает видеть {italic}{lvl} шт. карт{reset} и не может их использовать в течение следующего хода")

            if self.is_shell_shocked and not cyclone:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"СЛЕПОТА {lvl} 1 fc[]")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ТОРНАДО":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            self.opponent.status_effects.append(f"ОБЕЗОРУЖИВАНИЕ {lvl}")
            self.opponent.last_effect = "ОБЕЗОРУЖИВАНИЕ"
            rgb = '\033[38;2;169;193;199m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник сбрасывает {italic}{lvl} шт. карт")

            if treshold and lvl != 0:
                if treshold == 1:
                    if self.opponent.hand:  # Проверяем, что у противника есть карты
                        card = random.choice(self.opponent.hand)
                        color = get_color(card)
                        self.opponent.hand.remove(card)
                        self.hand.append(card)
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (9): {rgb}«СМЕРЧ»{reset}. Вы берёте в руку случайную карту противника — {color}{card}")
                    else:
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (9) (без эффекта):{reset} У противника нет карт для взятия")

                elif treshold == 2:
                    if self.opponent.hand:
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (10): {rgb}«СМЕРЧ»{reset}. Вы берёте в руку выбранную вами карту противника")
                        show_player_state(self.opponent, moves_counter)
                        print(f"\nВыберите карту, которую хотите взять, или «0» для отмены")

                        while True:
                            try:
                                num = input("\nВВОД:\n").strip()
                                if num == "0":
                                    print("\nВЫ НЕ СТАЛИ ВЫБИРАТЬ КАРТУ\n")
                                    break

                                num_index = int(num) - 1

                                if 0 <= num_index < len(self.opponent.hand):
                                    card = self.opponent.hand.pop(num_index)
                                    color = get_color(card)
                                    self.hand.append(card)
                                    print(f"\nПОЛУЧЕНА НОВАЯ КАРТА: {color}{card}\n")
                                    break
                                else:
                                    print(f"\nНЕВЕРНЫЙ НОМЕР КАРТЫ! Выберите от 1 до {len(self.opponent.hand)}")
                                    continue

                            except ValueError:
                                print("\nОШИБКА ВВОДА! Введите число")
                            except Exception as e:
                                print(f"\nОШИБКА: {e}")
                    else:
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (10) (без эффекта):{reset} У противника нет карт для взятия")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ОБЕЗОРУЖИВАНИЕ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "МОЛНИЯ":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            coeff = 1 if lvl == 2 else round(lvl / 2, 1)
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            self.opponent.status_effects.append(f"МОЛНИЯ {lvl}")
            if not cyclone:
                self.opponent.last_effect = "МОЛНИЯ"
            rgb = '\033[38;2;230;210;20m'
            if not cyclone:
                print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Молния стреляет в одну из самых сильных карт противника, заставляя её сбросить и наносит урон, равный силе этой карты, помноженной на {Style.BRIGHT}{italic}{coeff}")

            if treshold and lvl != 0:
                magic_dmg = math.ceil((len(list(filter(lambda x: "ВОДА" in x, self.opponent.hand)))) * 1.5)
                self.opponent.hp -= magic_dmg
                print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (>= 9): {rgb}«ЭЛЕКТРИЧЕСКАЯ ЦЕПЬ»{reset}. Наносит {italic}1.5-2 ед. урона{reset} противнику за каждую карту {italic}{get_color('ВОДА')}ВОДЫ{reset} в его руке. Итого: {italic}{magic_dmg} ед. урона")

            if self.is_shell_shocked and not cyclone:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    magic_dmg = len(self.last_move) * lvl
                    self.hp -= magic_dmg
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "МЕТЕОР":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ГОРЕНИЕ {lvl}")
            self.opponent.last_effect = "ГОРЕНИЕ"
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            case = 'ходов' if lvl >= 2 else 'хода'
            RGBs = ['\033[38;2;204;0;0m', '\033[38;2;214;42;0m']
            print(f"Вы применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник получает {italic}4 ед. урона{reset} в течение {italic}{lvl} {case}")

            if treshold and lvl != 0:
                amount = math.ceil(len(list(filter(lambda x: x.split()[0] == "ЗЕМЛЯ", self.opponent.hand))) / 2)
                counter = amount
                for i, card in enumerate(self.opponent.hand):
                    if counter == 0: break
                    if card.split()[0] == "ЗЕМЛЯ":
                        self.opponent.hand.pop(i)
                        counter -= 1
                print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (>= 9): {RGBs[1]}«ВЫЖЕННАЯ ЗЕМЛЯ»{reset}. Противник теряет {italic}{amount} шт. карт {get_color('ЗЕМЛЯ')}ЗЕМЛИ")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ГОРЕНИЕ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


    # ЭПИЧЕСКИЕ КОМБИНАЦИИ

        elif spell == "ЛАВИНА":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            exhaustion = 0.25 if lvl == 1 else 0.5
            duration = 2 if lvl == 3 else 1
            self.opponent.status_effects.append(f"ЗАВАЛ {exhaustion} {duration}")
            self.opponent.last_effect = "ЗАВАЛ"
            case = "ход" if lvl == 1 else "хода"
            rgb = '\033[38;2;120;122;89m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} Накладывает на противника «ИСТОЩЕНИЕ» {italic}{round(exhaustion * 100)}% на {duration} {case}")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник пропускает ход")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЗАВАЛ {exhaustion} {duration}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ЦИКЛОН":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ЦИКЛОН {lvl}")
            self.opponent.last_effect = "ЦИКЛОН"

            cyclone_rgb = '\033[38;2;224;224;224m'
            RGBs = ['\033[38;2;72;89;240m', '\033[38;2;204;229;255m', '\033[38;2;230;210;20m']
            case = "ход" if lvl == 1 else "хода"
            print(f"Вы применили заклинание {Style.BRIGHT}{cyclone_rgb}«{spell} {roman[str(lvl)]}»")
            print(f"Противник попадает в ЦИКЛОН на {italic}{lvl} {case}{reset}, который вызывает любое заклинание случайного уровня из следующих трёх: \
{Style.BRIGHT}{RGBs[0]}«ЦУНАМИ»{reset}, {Style.BRIGHT}{RGBs[1]}«ГЕЙЗЕР»{reset}, {Style.BRIGHT}{RGBs[2]}«МОЛНИЯ»{reset} — и применят на него")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЦИКЛОН {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{cyclone_rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "НАПАЛМ":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            duration = 3 if lvl == 3 else 2
            self.opponent.status_effects.append(f"НАПАЛМ {lvl} {duration}")
            self.opponent.last_effect = "НАПАЛМ"
            rgb = '\033[38;2;255;126;0m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} За каждую имеющуюся на руках карту {italic}{get_color('ОГОНЬ')}ОГНЯ{reset} наносит {italic}{lvl + 2} ед. урона")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} Накладывает на противника эффект «КОНТУЗИЯ» на {italic}{duration} хода,{reset} из-за чего он, применив заклинание на вас, может с вероятностью в 50% применить его также на себя")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"НАПАЛМ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ЗЕМЛЕТРЯСЕНИЕ":
            lvl = round(((dmg - 1) // 8 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ЗЕМЛЕТРЯСЕНИЕ {lvl}")
            self.opponent.last_effect = "ЗЕМЛЕТРЯСЕНИЕ"
            rgb = '\033[38;2;179;129;50m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник сбрасывает все карты {italic}силы {lvl + 1}{reset} или меньше")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} {rgb}«КОРРОЗИЯ»{reset}. Все карты противника теряют {italic}{math.ceil(lvl / 2)}{reset} ед. силы")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЗЕМЛЕТРЯСЕНИЕ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»{reset} на самого себя")


        elif spell == "ВЕЛИКАЯ КВИНТЭССЕНЦИЯ":
            lvl = round(((dmg - 1) // 8 + 1) * self.power_coeff)
            self.opponent.status_effects.append("None")
            rgb = '\033[38;2;202;32;252m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman[str(lvl)]}»")

            while True:
                effect = input(f"\nВЫБЕРИТЕ ЭФФЕКТ:\n\
{Style.BRIGHT}{Fore.BLUE}1){reset} Восстановление {italic}{4 + (lvl * 2)} ед. здоровья\n\
{Style.BRIGHT}{Fore.YELLOW}2){reset} Получение {italic}{1 + lvl} карт\n\
{Style.BRIGHT}{Fore.GREEN}3){reset} Барьер на {italic}{3 + lvl} единиц\n\
{Style.BRIGHT}{Fore.RED}4){reset} Нанесение {italic}{4 + (lvl * 2)} ед. урона\n\
{Style.BRIGHT}{Fore.WHITE}0){reset} Отмена заклинания\n")

                if effect == "0":
                    print(f"\nВЫ НЕ СТАЛИ ПРИМЕНЯТЬ ЗАКЛИНАНИЕ {rgb}«{spell}»")
                    break
                elif effect == "1":
                    regen = 4 + (lvl * 2)
                    heal(self, regen)
                    print(f"\nВы восстанавливаете себе {italic}{regen} ед. здоровья")
                    break
                elif effect == "2":
                    amount = 1 + lvl
                    self.hand += [deck.pop() for i in range(amount)]
                    print(f"\nВы получаете {italic}{amount} карт")
                    break
                elif effect == "3":
                    barrier = 3 + lvl
                    self.status_effects.append(f"БАРЬЕР {barrier}")
                    print(f"\nВы получаете БАРЬЕР на {italic}{barrier} ед.")
                    break
                elif effect == "4":
                    dmg = 4 + (lvl * 2)
                    self.opponent.hp -= dmg
                    print(f"\nВы наносите противнику {italic}{dmg} ед. урона")
                    break
                else:
                    continue