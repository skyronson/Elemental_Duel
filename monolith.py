import itertools as it
import functools
import math
import pandas as pd
import ast
import random
import time
from colorama import init, Fore, Back, Style

init(autoreset=True)


italic = '\033[3m'
reset = '\033[0;0m'


combinations = {
    'ЛЕЧЕНИЕ': ['ВОДА', 'ВОДА'],
    'ТЕЛЕКИНЕЗ': ['ВОЗДУХ', 'ВОЗДУХ'],
    'БАРЬЕР': ['ЗЕМЛЯ', 'ЗЕМЛЯ'],
    'ОГНЕННЫЙ ШАР': ['ОГОНЬ', 'ОГОНЬ'],
    'ЦУНАМИ': ['ВОДА', 'ВОЗДУХ'],
    'ГРЯЗЕВОЙ ПОТОП': ['ВОДА', 'ЗЕМЛЯ'],
    'ГЕЙЗЕР': ['ВОДА', 'ОГОНЬ'],
    'ТОРНАДО': ['ВОЗДУХ', 'ЗЕМЛЯ'],
    'МОЛНИЯ': ['ВОЗДУХ', 'ОГОНЬ'],
    'МЕТЕОР': ['ЗЕМЛЯ', 'ОГОНЬ'],
    'ЛАВИНА': ['ВОДА', 'ВОЗДУХ', 'ЗЕМЛЯ'],
    'ЦИКЛОН': ['ВОДА', 'ВОЗДУХ', 'ОГОНЬ'],
    'НАПАЛМ': ['ВОДА', 'ЗЕМЛЯ', 'ОГОНЬ'],
    'ЗЕМЛЕТРЯСЕНИЕ': ['ВОЗДУХ', 'ЗЕМЛЯ', 'ОГОНЬ'],
    'ВЕЛИКАЯ КВИНТЭССЕНЦИЯ': ['ВОДА', 'ВОЗДУХ', 'ЗЕМЛЯ', 'ОГОНЬ']
}


colors = {
    "ОГОНЬ": Fore.RED,
    "ВОДА": Fore.BLUE,
    "ЗЕМЛЯ": Fore.GREEN,
    "ВОЗДУХ": Fore.YELLOW,
    "ГРЯЗЬ": '\033[38;2;170;102;0m'
}


roman_literas = {
    0: '(без эффекта)',
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V',
}



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


    def set_name(self):
        name = input("Введите имя игрока: ")
        self.name = name



    def update_status(self, is_defended):
        global running, whoseTurn, moves_counter, deck
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
                RGBs = {"ЦУНАМИ": '\033[38;2;72;89;240m', "ГЕЙЗЕР": '\033[38;2;204;229;255m', "МОЛНИЯ": '\033[38;2;230;210;20m'}
                spell = random.choice(spells)
                lvl = 0
                if spell == "ГЕЙЗЕР":
                    lvl = random.choice(lvls + [4, 5])
                else:
                    lvl = random.choice(lvls)

                case = "ход" if duration == 1 else "хода"
                print(f"{Style.BRIGHT}{cyclone_rgb}«ЦИКЛОН»{reset} вызвал заклинание {Style.BRIGHT}{RGBs[spell]}«{spell} {roman_literas[lvl]}»{reset}. Осталось: {italic}{duration} {case}")
                if spell == "ГЕЙЗЕР":
                    self.opponent.cast_spell(spell, lvl * 4, cyclone=True)
                else:
                    self.opponent.cast_spell(spell, lvl * 7, cyclone=True)
                idx = self.status_effects.index(effect)
                self.status_effects[idx] = f"ЦИКЛОН {duration - 1}"


        if self.hp <= 0:
            running = end_game(self)
            return


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
                    self.status_effects_bar.add('🦨')
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
                        color = colors[card.split()[0]]
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
                    whoseTurn = abs(whoseTurn - 1)
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
                    self.opponent.status_effects.append(f"БАРЬЕР {lvl + 1}")
                    print(f"Ваш урон снижается на {italic}{lvl + 1} ед.{reset} на этом ходу")
                    self.status_effects.remove(effect)
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
            running = end_game(self)
            return

        names_of_effects = list(map(lambda x: x.split()[0], self.status_effects))

        if moves_counter > 2 and moves_counter % 10 != 0 and moves_counter % 10 != 1 and "ЗАВАЛ" not in names_of_effects:
            new_cards = draw_cards(2)
            self.hand.extend(new_cards)
            print(f"\nПОЛУЧЕНО 2 НОВЫХ КАРТЫ: ", end='')
            print(f"{colors[new_cards[0].split()[0]]} {new_cards[0]}", end=' +')
            print(f"{colors[new_cards[1].split()[0]]} {new_cards[1]}")

        elif moves_counter % 10 == 0:
            # Игрок берет карты
            new_cards = draw_cards(10)
            self.hand.extend(new_cards)
            # Противник тоже берет карты
            opponent_cards = draw_cards(10)
            self.opponent.hand.extend(opponent_cards)
            print("\nКАЖДЫЙ ИГРОК ПОЛУЧАЕТ 10 НОВЫХ КАРТ")



    def show(self):
        print(f"\n{moves_counter}. ""{:->20}".format(f" {self.name} ") + "{:-<300}\n".format(""))

        hand = ", ".join(self.hand)
        amount = len(self.hand)
        arr = list(map(str, range(1, amount + 1)))
        sym = " "

        for card in self.hand:
            length = len(card)
            mid = length // 2
            if len(str(arr[0])) == 1:
                print(sym * mid + arr.pop(0) + sym * (length - mid + 1), end='')
            else:
                print(sym * mid + arr.pop(0) + sym * (length - mid), end='')
        print('\n')

        for card in self.hand:
            for color in colors.keys():
                if color in card:
                    print(colors[color] + card, end='  ')
            if "???" in card:
                print(card, end='  ')

        print("\n")

        print(f"\nЗДОРОВЬЕ: {self.hp}")
        print("\n{:-^323}".format(""))



    def make_move(self, nums):
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
                for color in colors.keys():
                    if color in card:
                        if i != len(cards) - 1:
                            print(colors[color] + card, end=' + ')
                        else:
                            print(colors[color] + card)

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
                        self.cast_spell(spell, dmg)

            print("{:-^320}".format(""))
            return True

        else:
            print("\nВЫБРАНА НЕВЕРНАЯ КОМБИНАЦИЯ")
            return False



    def defend(self):
        if len(self.opponent.last_move) == 0:
            return

        print("\nПРЕДЫДУЩИЙ ХОД ПРОТИВНИКА: ", end=' ')
        for i, card in enumerate(self.opponent.last_move[:]):
            for color in colors.keys():
                if color in card:
                    if i != len(self.opponent.last_move) - 1:
                        print(colors[color] + card, end=' + ')
                    else:
                        print(colors[color] + card, end='')
        print()
        self.show()

        while True:
            nums = input("\nВЫБЕРИТЕ КАРТЫ, ЧТОБЫ ЗАЩИТИТЬСЯ:\n").strip()
            if nums == '':
                continue

            elif nums == '0':
                print("\nВЫ НЕ СТАЛИ ЗАЩИЩАТЬСЯ")
                last_move = list(map(lambda x: x.split()[0], self.opponent.last_move))
                show_message(self.opponent, last_move)
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
                            "🎯 Вы сделали это красиво, как в кино!"
                        ]
                        print(f"{Fore.CYAN}{random.choice(defense_messages)}{reset}")
                        time.sleep(2)
                        return True
                    else:
                        print(f"\nВЫ НЕУДАЧНО ОТРАЗИЛИ АТАКУ, ИТОГО ПОТЕРЯВ {italic}{abs(total_dmg - parried_dmg)} ед. здоровья")
                        last_move = list(map(lambda x: x.split()[0], self.opponent.last_move))
                        self.opponent.spells_counter += 1
                        # Шуточное сообщение при неудачной защите
                        show_message(self.opponent, last_move)
                        time.sleep(2)
                        return False

                except IndexError:
                    print(f"\nВЫБРАНЫ НЕВЕРНЫЕ КАРТЫ")
                    continue

            else:
                print("\nОШИБКА ВВОДА!")
                continue



    def cast_spell(self, spell, dmg, cyclone=False):
        global whoseTurn, roman_literas

        # ОРДИНАРНЫЕ КОМБИНАЦИИ

        if spell == 'ЛЕЧЕНИЕ':
            lvl = round(((dmg - 1) // 4 + 1) * self.power_coeff)
            heal(self, lvl)
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;255;255;188m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"Вы восстанавливаете себе {italic}{lvl} ед. здоровья")


        elif spell == 'ТЕЛЕКИНЕЗ':
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            new_cards = draw_cards(lvl)
            self.hand.extend(new_cards)
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;229;204;255m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"Вы берете {italic}{lvl} шт. карт")


        elif spell == 'БАРЬЕР':
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            self.status_effects.append(f"БАРЬЕР {lvl}")
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;144;165;39m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"Урон карт противника от атак снижается на {italic}{lvl} ед. на следующем ходу")


        elif spell == "ОГНЕННЫЙ ШАР":
            lvl = round(((dmg - 1) // 4 + 1) * self.power_coeff)
            self.opponent.hp -= lvl
            self.opponent.last_effect = "None"
            rgb = '\033[38;2;255;199;18m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
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

            if (self == player_1 and whoseTurn) or (self == player_2 and not whoseTurn):
                if lvl != 0:
                    self.show()
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
                                self.hand.extend(draw_cards(1))

                            print(f"\nПОЛУЧЕНЫ НОВЫЕ КАРТЫ: ", end='')

                            for i, card in enumerate(self.hand[(-length):]):
                                for color in colors.keys():
                                    if color in card:
                                        if i != length - 1:
                                            print(colors[color] + card, end=', ')
                                        else:
                                            print(colors[color] + card, end='\n\n')
                            break  # ← ВАЖНО: ВЫХОДИМ ИЗ ЦИКЛА ПОСЛЕ УСПЕШНОЙ ЗАМЕНЫ

                        except ValueError:
                            print("\nОШИБКА ВВОДА! Введите числа через пробел")
                        except Exception as e:
                            print(f"ОШИБКА! {e}")

                print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Снижает мощность заклинаний противника на {italic}{int((1 - self.opponent.power_coeff) * 100)}%{reset} на следующем ходу")

            if heads_or_tails and not cyclone:
                self.status_effects.append("ИСТОЩЕНИЕ 1")
                print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "ГРЯЗЕВОЙ ПОТОП":
            lvl = round(((dmg - 1) // 5 + 1) * self.power_coeff)
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            self.opponent.status_effects.append(f"ГРЯЗНУЛЯ {lvl}")
            self.opponent.last_effect = "ГРЯЗНУЛЯ"
            rgb = '\033[38;2;170;102;0m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Заменяет {italic}{lvl} шт. карт{reset} в колоде противника на ГРЯЗЬ с пониженными вдвое характеристиками")

            if treshold and lvl != 0:
                for i in range(len(self.opponent.hand)):
                    try:
                        card = self.opponent.hand[i]
                        if card != '   ???   ':
                            element, power = card.split()
                            new_power = max(1, int(power) - treshold)
                            self.opponent.hand[i] = f"{element} {new_power}"
                    except (ValueError, IndexError) as e:
                        print(e)
                        continue
                print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (>= 9): {rgb}«ПОРЧА»{reset}. Все карты противника теряют {italic}{treshold} ед. силы")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ГРЯЗНУЛЯ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


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
            if not cyclone:
                self.opponent.last_effect = "СЛЕПОТА"
            RGBs = ['\033[38;2;204;229;255m', '\033[38;2;18;255;167m']
            if (self == player_1 and whoseTurn) or (self == player_2 and not whoseTurn):
                print(f"Вы применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman_literas[lvl]}»")
                print(f"{Style.BRIGHT}ПАССИВНАЯ СПОСОБНОСТЬ: {RGBs[1]}«ДЫХАНИЕ ДРАКОНА»{reset}. Все карты {italic}{colors['ВОЗДУХ']}ВОЗДУХА{reset} в вашей руке получают {italic}+{add_power} к силе")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Накладывает на противника эффект «СЛЕПОТА», из-за чего он перестает видеть {italic}{lvl} шт. карт{reset} и не может их использовать в течение следующего хода")

            if self.is_shell_shocked and not cyclone:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"СЛЕПОТА {lvl} 1 fc[]")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "ТОРНАДО":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            self.opponent.status_effects.append(f"ОБЕЗОРУЖИВАНИЕ {lvl}")
            self.opponent.last_effect = "ОБЕЗОРУЖИВАНИЕ"
            rgb = '\033[38;2;169;193;199m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник сбрасывает {italic}{lvl} шт. карт")

            if treshold and lvl != 0:
                if treshold == 1:
                    if self.opponent.hand:  # Проверяем, что у противника есть карты
                        card = random.choice(self.opponent.hand)
                        self.opponent.hand.remove(card)
                        self.hand.append(card)
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (9): {rgb}«СМЕРЧ»{reset}. Вы берёте в руку случайную карту противника — {colors[card.split()[0]]}{card}")
                    else:
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (9) (без эффекта):{reset} У противника нет карт для взятия")

                elif treshold == 2:
                    if self.opponent.hand:
                        print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (10): {rgb}«СМЕРЧ»{reset}. Вы берёте в руку выбранную вами карту противника")
                        self.opponent.show()
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
                                    self.hand.append(card)
                                    print(f"\nПОЛУЧЕНА НОВАЯ КАРТА: {colors[card.split()[0]]}{card}\n")
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
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


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
            if (self == player_1 and whoseTurn) or (self == player_2 and not whoseTurn):
                print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
                print(f"{Style.BRIGHT}ШТРАФ:{reset} Молния стреляет в одну из самых сильных карт противника, заставляя её сбросить и наносит урон, равный силе этой карты, помноженной на {Style.BRIGHT}{italic}{coeff}")

            if treshold and lvl != 0:
                magic_dmg = math.ceil((len(list(filter(lambda x: "ВОДА" in x, self.opponent.hand)))) * 1.5)
                self.opponent.hp -= magic_dmg
                print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (>= 9): {rgb}«ЭЛЕКТРИЧЕСКАЯ ЦЕПЬ»{reset}. Наносит {italic}1.5-2 ед. урона{reset} противнику за каждую карту {italic}{colors['ВОДА']}ВОДЫ{reset} в его руке. Итого: {italic}{magic_dmg} ед. урона")

            if self.is_shell_shocked and not cyclone:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    magic_dmg = len(self.last_move) * lvl
                    self.hp -= magic_dmg
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "МЕТЕОР":
            lvl = round(((dmg - 1) // 7 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ГОРЕНИЕ {lvl}")
            self.opponent.last_effect = "ГОРЕНИЕ"
            treshold = 0
            if dmg >= 18:
                treshold = abs(8 - (dmg // 2))
            case = 'ходов' if lvl >= 2 else 'хода'
            RGBs = ['\033[38;2;204;0;0m', '\033[38;2;214;42;0m']
            print(f"Вы применили заклинание {Style.BRIGHT}{RGBs[0]}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник получает {italic}4 ед. урона{reset} в течение {italic}{lvl} {case}")

            if treshold and lvl != 0:
                amount = math.ceil(len(list(filter(lambda x: x.split()[0] == "ЗЕМЛЯ", self.opponent.hand))) / 2)
                counter = amount
                for i, card in enumerate(self.opponent.hand):
                    if counter == 0: break
                    if card.split()[0] == "ЗЕМЛЯ":
                        self.opponent.hand.pop(i)
                        counter -= 1
                print(f"{Style.BRIGHT}ПОРОГОВЫЙ ЭФФЕКТ (>= 9): {RGBs[1]}«ВЫЖЕННАЯ ЗЕМЛЯ»{reset}. Противник теряет {italic}{amount} шт. карт {colors['ЗЕМЛЯ']}ЗЕМЛИ")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ГОРЕНИЕ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{RGBs[1]}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


    # ЭПИЧЕСКИЕ КОМБИНАЦИИ

        elif spell == "ЛАВИНА":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            exhaustion = 0.25 if lvl == 1 else 0.5
            duration = 2 if lvl == 3 else 1
            self.opponent.status_effects.append(f"ЗАВАЛ {exhaustion} {duration}")
            self.opponent.last_effect = "ЗАВАЛ"
            case = "ход" if lvl == 1 else "хода"
            rgb = '\033[38;2;120;122;89m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} Накладывает на противника «ИСТОЩЕНИЕ» {italic}{round(exhaustion * 100)}% на {duration} {case}")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник пропускает ход")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЗАВАЛ {exhaustion} {duration}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "ЦИКЛОН":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ЦИКЛОН {lvl}")
            self.opponent.last_effect = "ЦИКЛОН"

            cyclone_rgb = '\033[38;2;224;224;224m'
            RGBs = ['\033[38;2;72;89;240m', '\033[38;2;204;229;255m', '\033[38;2;230;210;20m']
            case = "ход" if lvl == 1 else "хода"
            print(f"Вы применили заклинание {Style.BRIGHT}{cyclone_rgb}«{spell} {roman_literas[lvl]}»")
            print(f"Противник попадает в ЦИКЛОН на {italic}{lvl} {case}{reset}, который вызывает любое заклинание случайного уровня из следующих трёх: \
{Style.BRIGHT}{RGBs[0]}«ЦУНАМИ»{reset}, {Style.BRIGHT}{RGBs[1]}«ГЕЙЗЕР»{reset}, {Style.BRIGHT}{RGBs[2]}«МОЛНИЯ»{reset} — и применят на него")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЦИКЛОН {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{cyclone_rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "НАПАЛМ":
            lvl = round(((dmg - 1) // 10 + 1) * self.power_coeff)
            duration = 3 if lvl == 3 else 2
            self.opponent.status_effects.append(f"НАПАЛМ {lvl} {duration}")
            self.opponent.last_effect = "НАПАЛМ"
            rgb = '\033[38;2;255;126;0m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} За каждую имеющуюся на руках карту огня наносит {italic}{lvl + 2} ед. урона")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} Накладывает на противника эффект «КОНТУЗИЯ» на {italic}{duration} хода,{reset} из-за чего он, применив заклинание на вас, может с вероятностью в 50% применить его также на себя")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"НАПАЛМ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "ЗЕМЛЕТРЯСЕНИЕ":
            lvl = round(((dmg - 1) // 8 + 1) * self.power_coeff)
            self.opponent.status_effects.append(f"ЗЕМЛЕТРЯСЕНИЕ {lvl}")
            self.opponent.last_effect = "ЗЕМЛЕТРЯСЕНИЕ"
            rgb = '\033[38;2;179;129;50m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")
            print(f"{Style.BRIGHT}ШТРАФ:{reset} Противник сбрасывает все карты {italic}силы {lvl + 1}{reset} или меньше")
            print(f"{Style.BRIGHT}ОТРАЖЕНО:{reset} Урон карт противника от атак снижается на {italic}{lvl + 1} ед.{reset} на следующем ходу")

            if self.is_shell_shocked:
                heads_or_tails = random.randint(0, 1)
                if heads_or_tails:
                    self.status_effects.append(f"ЗЕМЛЕТРЯСЕНИЕ {lvl}")
                    print(f"Вы случайно применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»{reset} на самого себя")


        elif spell == "ВЕЛИКАЯ КВИНТЭССЕНЦИЯ":
            lvl = round(((dmg - 1) // 8 + 1) * self.power_coeff)
            self.opponent.status_effects.append("None")
            rgb = '\033[38;2;202;32;252m'
            print(f"Вы применили заклинание {Style.BRIGHT}{rgb}«{spell} {roman_literas[lvl]}»")

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





# Функция для безопасного взятия карт из колоды
def draw_cards(count):
    drawn = []
    for i in range(count):
        if len(deck) == 0:
            refill_deck()  # Перезаполняем колоду если она пустая
        if len(deck) > 0:
            drawn.append(deck.pop())
    return drawn



# Функция для обновления колоды карт, когда они заканчиваются
def refill_deck():
    global deck
    deck = it.product(elements, numbers)
    deck = list(map(lambda i: " ".join(i), deck))
    random.shuffle(deck)
    print("\nКОЛОДА ОБНОВЛЕНА")



def heal(target, value):
    if value < target.max_hp - target.hp:
        target.hp += value
    else:
        target.hp = target.max_hp


def show_message(enemy, elements_used):
    # ШУТОЧНЫЕ СООБЩЕНИЯ ДЛЯ РАЗНЫХ КОМБИНАЦИЙ КАРТ
    # Комбинации с ОГНЕМ
    if all(map(lambda x: x == "ОГОНЬ", elements_used)) and len(set(elements_used)) == 1:
        fire_messages = [
            f"🔥 {enemy.name} подпалил вам усики!",
            f"🔥 {enemy.name} устроил небольшой костерок на вашей голове!",
            f"🔥 {enemy.name} поджарил вам брови!",
            f"🔥 От {enemy.opponent.name} пахнет жареным!",
            f"🔥 {enemy.name} решил сделать вам 'горячий' прием!",
            f"🔥 {enemy.name} запустил в вас шашлычный шампур!",
            f"🔥 {enemy.name} поджарил вам пятую точку!",

        ]
        print(f"{Fore.RED}{random.choice(fire_messages)}{reset}")

    # Комбинации с ВОДОЙ
    if all(map(lambda x: x == "ВОДА", elements_used)) and len(set(elements_used)) == 1:
        water_messages = [
            f"💧 {enemy.name} устроил вам внезапный душ!",
            f"💧 {enemy.name} намочил вам носки!",
            f"💧 От {enemy.opponent.name} пахнет свежестью и мокрой собакой!",
            f"💧 {enemy.opponent.name} помылся впервые за месяц"
            f"💧 {enemy.name} решил вас 'освежить'!",
            f"💧 {enemy.name} запустил вам в лицо водяной пистолет!"
        ]
        print(f"{Fore.BLUE}{random.choice(water_messages)}{reset}")

    # Комбинации с ВОЗДУХОМ
    if all(map(lambda x: x == "ВОЗДУХ", elements_used)) and len(set(elements_used)) == 1:
        air_messages = [
            f"💨 {enemy.name} устроил вам прическу 'ветер в голове'!",
            f"💨 {enemy.name} запустил вам за шиворот порыв ветра!",
            f"💨 От {enemy.opponent.name} пахнет свежим бризом и испугом!",
            f"💨 {enemy.name} решил проветрить ваши мозги!",
            f"💨 {enemy.name} устроил вам внеплановую сушку феном!"
        ]
        print(f"{Fore.YELLOW}{random.choice(air_messages)}{reset}")

    # Комбинации с ЗЕМЛЕЙ
    if all(map(lambda x: x == "ЗЕМЛЯ", elements_used)) and len(set(elements_used)) == 1:
        earth_messages = [
            f"🌱 {enemy.name} засыпал вам карманы землей!",
            f"🌱 {enemy.name} устроил вам песочную ванну!",
            f"🌱 От {enemy.opponent.name} пахнет свежевскопанной грядкой!",
            f"🌱 {enemy.name} решил вас 'заземлить'!",
            f"🌱 {enemy.name} подкинул вам грязи в ботинки!"
        ]
        print(f"{Fore.GREEN}{random.choice(earth_messages)}{reset}")

    # ШУТОЧНЫЕ СООБЩЕНИЯ ДЛЯ ЗАКЛИНАНИЙ
    spell_messages = {
        'ЦУНАМИ': [
            f"🌊 {enemy.name} устроил вам стирку без порошка!",
            f"🌊 {enemy.name} запустил в вас аквадискотеку!",
            f"🌊 От {enemy.opponent.name} пахнет морской болезнью!"
        ],
        'ГРЯЗЕВОЙ ПОТОП': [
            f"🦨 {enemy.name} испачкал вам белые штаны!",
            f"🦨 {enemy.name} устроил грязевые ванны!",
            f"🦨 От {enemy.opponent.name} пахнет весной в деревне!"
        ],
        'ГЕЙЗЕР': [
            f"💦 {enemy.name} устроил вам внезапный фонтан!",
            f"💦 {enemy.name} запустил паровую баню!",
            f"💦 От {enemy.opponent.name} пахнет бассейном и хлоркой!"
        ],
        'МОЛНИЯ': [
            f"⚡ {enemy.name} устроил вам пытку на электрическом стуле!",
            f"⚡ {enemy.name} зарядил вас как батарейку!",
            f"⚡ От {enemy.opponent.name} пахнет жареной котлетой!"
        ],
        'ТОРНАДО': [
            f"🌪️ {enemy.name} устроил вам денежный вихрь из ваших же денег!",
            f"🌪️ {enemy.name} запутал все ваши мысли!",
            f"🌪️ От {enemy.opponent.name} пахнет пылью и хаосом!"
        ],
        'МЕТЕОР': [
            f"☄️ {enemy.name} сбросил на вас космический мусор!",
            f"☄️ {enemy.name} устроил звездопад по голове!",
            f"☄️ От {enemy.opponent.name} пахнет метеоритной пылью!"
        ],
        'ЛАВИНА': [
            f"🏔️ {enemy.name} засыпал вас снежнинками!",
            f"🏔️ {enemy.name} устроил зимние игры в июле!",
            f"🏔️ От {enemy.opponent.name} пахнет мятным леденцом и холодком!"
        ],
        'ЦИКЛОН': [
            f"🌀 {enemy.name} запустил вас в центрифугу!",
            f"🌀 {enemy.name} устроил карусель из ваших мозгов!",
            f"🌀 От {enemy.opponent.name} пахнет вертолетом и тошнотой!"
        ],
        'НАПАЛМ': [
            f"💥 {enemy.name} устроил вам вьетнамские джунгли!",
            f"💥 {enemy.name} поджарил вас со всех сторон!",
            f"💥 От {enemy.opponent.name} пахнет бензином и приключениями!"
        ],
        'ЗЕМЛЕТРЯСЕНИЕ': [
            f"🏚️ {enemy.name} потанцевал на вашем полу!",
            f"🏚️ {enemy.name} устроил тест на сейсмоустойчивость!",
            f"🏚️ От {enemy.opponent.name} пахнет пылью и ремонтом!"
        ],
        'ВЕЛИКАЯ КВИНТЭССЕНЦИЯ': [
            f"🌈 {enemy.name} устроил магический фейерверк!",
            f"🌈 {enemy.name} показал вам все цвета радуги!",
            f"🌈 От {enemy.opponent.name} пахнет волшебством и нафталином!"
        ]
    }

    spell = ""
    for combination in combinations.items():
        if combination[1] == sorted(elements_used):
            spell = combination[0]

    if spell in spell_messages:
        print(f"{Style.BRIGHT}{random.choice(spell_messages[spell])}{reset}")



def play(player):
    global moves_counter, whoseTurn
    while True:
        action = input("\nАТАКА:\n").strip()

        if len(action.split()) == 0:  # Проверка, если введена пустая строка
            continue

        elif action == "\help":
            help()
            ok = input()
            player.show()
            continue

        elif action == "\\rules" or action == '322':
            rules()
            ok = input()
            player.show()
            continue

        elif action == "\deck":
            print(deck)
            print(f"КОЛ-ВО КАРТ: {len(deck)}")
            ok = input()
            continue

        elif action == '\end' or action == '0':
            print("\nХОД ОКОНЧЕН")
            print("\n{:-^320}".format(""))
            player.last_move = []
            time.sleep(3)
            whoseTurn = 0 if player == player_1 else 1
            moves_counter += 1
            return True

        elif action == "\qqq":
            print("\n{:->20}".format(f" КОНЕЦ ИГРЫ ") + "{:-<300}\n".format(""))
            return False

        elif all(map(lambda i: i.isdigit(), action.split())):
            try:
                success = player.make_move(action)
                if success:
                    while True:
                        action = input("\n")
                        if action == "\help":
                            help()
                            ok = input()
                            player.show()
                            continue
                        elif action == "\deck":
                            print(deck)
                            print(f"КОЛ-ВО КАРТ: {len(deck)}")
                            ok = input()
                            continue
                        elif action == '\end' or action == '0':
                            print("\nХОД ОКОНЧЕН")
                            print("\n{:-^320}".format(""))
                            time.sleep(3)
                            whoseTurn = 0 if player == player_1 else 1
                            moves_counter += 1
                            return True
                        elif action == "\qqq":
                            print("\n{:->20}".format(f" КОНЕЦ ИГРЫ ") + "{:-<300}\n".format(""))
                            return False
                        else:
                            print("\nОШИБКА ВВОДА!")
                            continue
            except IndexError:
                print(f"\nВЫБРАНЫ НЕВЕРНЫЕ КАРТЫ")
                continue

        else:
            print("\nОШИБКА ВВОДА!")
            continue



def help():
    print("\n{:->20}".format(f" КОМАНДЫ ") + "{:-<300}\n".format(""))

    print("1-? — выбор карты")
    print("\end или 0 — завершить ход")
    print("\qqq — закончить игру")
    print("\deck — показать имеющиеся в колоде карты")
    print("\\rules или 322 — правила игры")

    print("\n{:-^320}".format(""))



def rules():
    print("\n4 ЦВЕТА, СИМВОЛИЗИРУЮЩИЕ СТИХИИ:\n\
СИНИЙ — ВОДА\n\
ЖЁЛТЫЙ — ВОЗДУХ\n\
ЗЕЛЁНЫЙ — ЗЕМЛЯ\n\
КРАСНЫЙ — ОГОНЬ\n\
\n\
ПЕРВЫЙ ИГРОК БЕРЁТ 8 КАРТ НА РУКУ, ВТОРОЙ БЕРЁТ 10 КАРТ — ЭТО ВАШИ СТАРТОВЫЕ КАРТЫ, И КАЖДЫЙ НАЧИНАЕТ ИГРУ С 50 ЕДИНИЦАМИ ЗДОРОВЬЯ\n\
КАЖДЫЙ 10 ХОД ОБА ИГРОКА ПОЛУАЮТ 10 НОВЫХ КАРТ\n\
КАЖДЫЙ ХОД ИГРОК МОЖЕТ РАЗЫГРАТЬ ЛИБО ОТ 1 ДО 4 КАРТ ОДНОГО ДОСТОИНСТВА (например, 4 четверки),\n\
ЛИБО ДВЕ КАРТЫ ОДНОГО ЦВЕТА (например ВОДА 1 и ВОДА 5)...\n\
...ДЛЯ ТОГО, ЧТОБЫ АТАКОВАТЬ ПРОТИВНИКА\n\
УРОН ВАШЕЙ АТАКИ БУДЕТ РАВЕН СУММЕ ВСЕХ ЦИФР НА КАРТАХ, КОТОРЫЕ ВЫ РАЗЫГРАЛИ\n\
(например если вы разыграли карты «ОГОНЬ 9» + «ЗЕМЛЯ 9», то ваша атака нанесет 9 + 9 = 18 ед. урона)\n\
ПОСЛЕ КАЖДОГО ХОДА ИГРОК БЕРЕТ 2 КАРТЫ\n\
ПОСЛЕ ТОГО, КАК 1 ИГРОК СХОДИЛ, 2 ИГРОК МОЖЕТ ЗАЩИТИТЬСЯ ОТ АТАКИ, ПОКРЫВ КАЖДУЮ КАРТУ ПРОТИВНИКА СВОЕЙ\n\
\n\
ВОДА ПОГЛОЩАЕТ ЗЕМЛЮ С СООТНОШЕНИЕМ 2:1, ОГОНЬ 1:1 И ВОЗДУХ 1:2\n\
ВОЗДУХ ПОГЛОЩАЕТ ВОДУ С СООТНОШЕНИЕМ 2:1, ЗЕМЛЮ 1:1 И ОГОНЬ 1:2\n\
ЗЕМЛЯ ПОГЛОШАЕТ ОГОНЬ С СООТНОШЕНИЕМ 2:1, ВОЗДУХ 1:1 И ВОДУ 1:2\n\
ОГОНЬ ПОГЛОЩАЕТ ВОЗДУХ С СООТНОШЕНИЕМ 2:1, ВОДУ 1:1 И ЗЕМЛЮ 1:2\n\
\n\
Это значит, что если, условно, игрок А кинет карту ВОДЫ (синюю) с цифрой 5, то игрок B может её перекрыть одним из следующих способов:\n\
1) сыграть карту ОГНЯ с цифрой 5 или больше;\n\
2) сыграть карту ЗЕМЛИ с цифрой в два раза больше 5, т.е. 10, т.к. ЗЕМЛЯ в два раза слабее ВОДЫ при поглощении;\n\
3) сыграть карту ВОЗДУХА с цифрой 3 или больше, т.к. ВОЗДУХ в два раза сильнее работает против ВОДЫ\n\
\n\
ПОСЛЕ ЭТОГО 2 ИГРОК НАЧИНАЕТ САМ АТАКУ НА 1 ИГРОКА\n\
ИТАК ДО ТЕХ ПОР, ПОКА ОДИН ИЗ ИГРОКОВ НЕ ЛИШИТСЯ ВСЕГО КОЛИЧЕСТВА ЗДОРОВЬЯ")



def end_game(loser):
    try:
        from utils.data_loader import load_leaderboard, load_to_leaderboard
        data = load_leaderboard()
        new_points = 25 + (3 - moves_counter // 10) + (loser.opponent.hp // 10) + (loser.opponent.spells_counter // 5)

        players = [
            {'name': loser.opponent.name, 'is_winner': True},
            {'name': loser.name, 'is_winner': False}
        ]

        for player in players:
            name = player['name']
            is_winner = player['is_winner']

            # Поиск игрока в таблице
            if name in data['Nickname'].values:
                idx = data[data['Nickname'] == name].index[0]
            else:
                # Добавление нового игрока
                new_row = pd.DataFrame({
                    'Nickname': [name],
                    'Matches': [0],
                    'Victories': [0],
                    'Winrate': ['0%'],
                    'Rating': [1000]
                })
                data = pd.concat([data, new_row], ignore_index=True)
                idx = data[data['Nickname'] == name].index[0]

            # Обновление статистики
            data.at[idx, 'Matches'] += 1
            if is_winner:
                data.at[idx, 'Victories'] += 1
                data.at[idx, 'Rating'] += new_points
            else:
                data.at[idx, 'Rating'] = max(0, data.at[idx, 'Rating'] - 20)

            # Пересчет винрейта
            victories = data.at[idx, 'Victories']
            matches = data.at[idx, 'Matches']
            winrate = round((victories / matches) * 100) if matches > 0 else 0
            data.at[idx, 'Winrate'] = f"{winrate}%"

        # Сохранение данных
        load_to_leaderboard(data)

        # ... вывод сообщений ...
        print()
        print(f"ИГРОК {loser.name} ПРОИГРАЛ")
        time.sleep(1)
        print(f"НЕ РАССТРАИВАЙТЕСЬ! В СЛЕДУЮЩИЙ РАЗ ПОВЕЗЁТ")
        time.sleep(1)
        print(f"ПОЗДРАВЛЯЕМ ИГРОКА {loser.opponent.name} С ПОБЕДОЙ!")
        time.sleep(1)
        print(f"ОН ПОЛУЧАЕТ +{new_points} ОЧКОВ РЕЙТИНГА")
        time.sleep(1)
        print("\n{:->20}".format(f" КОНЕЦ ИГРЫ ") + "{:-<300}\n".format(""))

    except Exception as e:
        print(f"Ошибка при обновлении статистики: {e}")


    return False


"""--------- ПОДГОТОВКА К ИГРЕ -----------------------------------------------------------------------------------"""


running = True

elements = ["ОГОНЬ", "ВОДА", "ЗЕМЛЯ", "ВОЗДУХ"] * 2
numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
special_cards = ["РИТУАЛЬНЫЙ СВИТОК" * 8, "ФОЛИАНТ ТЬМЫ", "ФОЛИАНТ СВЕТА", "КРЫЛЬЯ", "ЗАЧАРОВАННОЕ ЗЕРКАЛО", "«МОПСОВОРОТ»", "«КРУГОВЕРТЬ ПУСТОТЫ»"]

deck = it.product(elements, numbers)
deck = list(map(lambda i: " ".join(i), deck))
random.shuffle(deck)

whoseTurn = 1
moves_counter = 1

player_1 = Player()
player_2 = Player()
player_1.opponent = player_2
player_2.opponent = player_1

for i in range(10):
    if i <= 7:
        player_1.hand.append(deck.pop())
    player_2.hand.append(deck.pop())

"""--------- НАЧАЛО ИГРЫ --------------------------------------------------------------------------------------------"""


# loading = iter("ЗАГРУЗКА")
# colors_for_loading = it.cycle([Fore.BLUE, Fore.YELLOW, Fore.GREEN, Fore.RED, Fore.MAGENTA,
# '\033[38;2;255;255;188m', '\033[38;2;229;204;255m', '\033[38;2;144;165;39m', '\033[38;2;255;199;18m', '\033[38;2;72;89;240m',
# '\033[38;2;170;102;0m', '\033[38;2;204;229;255m', '\033[38;2;18;255;167m', '\033[38;2;169;193;199m', '\033[38;2;230;210;20m',
# '\033[38;2;204;0;0m', '\033[38;2;120;122;89m', '\033[38;2;224;224;224m', '\033[38;2;255;126;0m', '\033[38;2;179;129;50m', '\033[38;2;202;32;252m'])
# print("\n")
# for i in range(200):
#     if 90 < i < 99:
#         print(f"{next(colors_for_loading)}▓", end=' ')
#         print(next(loading), end=' ')
#     else:
#         print(f"▓", end='')
#     time.sleep(0.008)
# print("\n")

player_1.set_name()
player_2.set_name()

while running:

    # 1) ХОД ПЕРВОГО ИГРОКА

    if whoseTurn:
        success = True
        if moves_counter > 1:
            success = player_1.defend()
        player_1.update_status(success)

        if not running:
            break

        if whoseTurn == 0:
            moves_counter += 1
            continue

        player_1.show()
        go_next = play(player_1)
        if not go_next:
            break


    # 2) ХОД ВТОРОГО ИГРОКА

    else:
        success = player_2.defend()
        player_2.update_status(success)

        if not running:
            break

        if whoseTurn:
            moves_counter += 1
            continue

        player_2.show()
        go_next = play(player_2)
        if not go_next:
            break
