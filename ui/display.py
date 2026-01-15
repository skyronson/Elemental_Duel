from colorama import init, Fore, Back, Style
from utils.helpers import get_color
from utils.data_loader import load_elements
import random
import time


init(autoreset=True)
italic = '\033[3m'
reset = '\033[0;0m'


def show_new_cards_message(new_cards):
    amount = len(new_cards)
    if amount == 0:
        return
    elif amount == 1:
        card = new_cards[0]
        print(f"\nПОЛУЧЕНА НОВАЯ КАРТА: {get_color(card)} {card}")
    elif amount == 2:
        print(f"\nПОЛУЧЕНО 2 НОВЫХ КАРТЫ: ", end='')
        print(f"{get_color(new_cards[0])} {new_cards[0]}", end=' +')
        print(f"{get_color(new_cards[1])} {new_cards[1]}")
    else:
        print("\nКАЖДЫЙ ИГРОК ПОЛУЧАЕТ ДО 10 НОВЫХ КАРТ")


def show_player_state(player, moves_counter):
    colors = load_elements()['colors']
    print(f"\n{moves_counter}. {'-'*20} {player.name} {'-'*300}\n")

    hand = player.hand
    amount = len(hand)
    arr = list(map(str, range(1, amount + 1)))
    sym = " "

    for card in hand:
        length = len(card)
        mid = length // 2
        if len(str(arr[0])) == 1:
            print(sym * mid + arr.pop(0) + sym * (length - mid + 1), end='')
        else:
            print(sym * mid + arr.pop(0) + sym * (length - mid), end='')
    print('\n')

    for card in hand:
        col = get_color(card)
        print(f"{col}{card}", end='  ')

    print("\n")
    print(f"\nЗДОРОВЬЕ: {player.hp}")
    print("\n{:-^323}".format(""))


def show_combat_message(attacker, elements_used):
    # ШУТОЧНЫЕ СООБЩЕНИЯ ДЛЯ РАЗНЫХ КОМБИНАЦИЙ КАРТ
    from utils.data_loader import load_combinations

    # Комбинации с ОГНЕМ
    if all(map(lambda x: x == "ОГОНЬ", elements_used)) and len(set(elements_used)) == 1:
        fire_messages = [
            f"🔥 {attacker.name} подпалил вам бороду!",
            f"🔥 {attacker.name} устроил небольшой костерок на вашей голове!",
            f"🔥 {attacker.name} поджарил вам брови!",
            f"🔥 От {attacker.opponent.name} пахнет жареным!",
            f"🔥 {attacker.name} решил сделать вам 'горячий' прием!",
            f"🔥 {attacker.name} запустил в вас шашлычный шампур!",
            f"🔥 {attacker.name} поджарил вам пятую точку!",

        ]
        print(f"{Fore.RED}{random.choice(fire_messages)}{reset}")

    # Комбинации с ВОДОЙ
    if all(map(lambda x: x == "ВОДА", elements_used)) and len(set(elements_used)) == 1:
        water_messages = [
            f"💧 {attacker.name} устроил вам внезапный душ!",
            f"💧 {attacker.name} намочил вам носки!",
            f"💧 От {attacker.opponent.name} пахнет свежестью и мокрой собакой!",
            f"💧 {attacker.opponent.name} помылся впервые за месяц",
            f"💧 {attacker.name} решил вас 'освежить'!",
            f"💧 {attacker.name} запустил вам в лицо водяной пистолет!"
        ]
        print(f"{Fore.BLUE}{random.choice(water_messages)}{reset}")

    # Комбинации с ВОЗДУХОМ
    if all(map(lambda x: x == "ВОЗДУХ", elements_used)) and len(set(elements_used)) == 1:
        air_messages = [
            f"💨 {attacker.name} устроил вам прическу 'ветер в голове'!",
            f"💨 {attacker.name} запустил вам за шиворот порыв ветра!",
            f"💨 От {attacker.opponent.name} пахнет свежим бризом и испугом!",
            f"💨 {attacker.name} решил проветрить ваши мозги!",
            f"💨 {attacker.name} устроил вам внеплановую сушку феном!"
        ]
        print(f"{Fore.YELLOW}{random.choice(air_messages)}{reset}")

    # Комбинации с ЗЕМЛЕЙ
    if all(map(lambda x: x == "ЗЕМЛЯ", elements_used)) and len(set(elements_used)) == 1:
        earth_messages = [
            f"🌱 {attacker.name} засыпал вам карманы землей!",
            f"🌱 {attacker.name} устроил вам песочную ванну!",
            f"🌱 От {attacker.opponent.name} пахнет свежевскопанной грядкой!",
            f"🌱 {attacker.name} решил вас 'заземлить'!",
            f"🌱 {attacker.name} подкинул вам грязи в ботинки!"
        ]
        print(f"{Fore.GREEN}{random.choice(earth_messages)}{reset}")

    spell_messages = {
        'ЦУНАМИ': [
            f"🌊 {attacker.name} устроил(а) вам стирку без порошка!",
            f"🌊 {attacker.name} запустил(а) в вас аквадискотеку!",
            f"🌊 От {attacker.opponent.name} пахнет морской болезнью!"
        ],
        'ГРЯЗЕВОЙ ПОТОП': [
            f"🦨 {attacker.name} испачкал(а) вам белые штаны!",
            f"🦨 {attacker.name} устроил(а) вам грязевые ванны!",
            f"🦨 От {attacker.opponent.name} пахнет весной в деревне!"
        ],
        'ГЕЙЗЕР': [
            f"💦 {attacker.name} устроил(а) вам внезапный фонтан!",
            f"💦 {attacker.name} запустил(а) паровую баню!",
            f"💦 От {attacker.opponent.name} пахнет бассейном и хлоркой!"
        ],
        'МОЛНИЯ': [
            f"⚡ {attacker.name} устроил(а) вам пытку на электрическом стуле!",
            f"⚡ {attacker.name} зарядил(а) вас как батарейку!",
            f"⚡ От {attacker.opponent.name} пахнет жареной котлетой!"
        ],
        'ТОРНАДО': [
            f"🌪️ {attacker.name} устроил(а) вам денежный вихрь из ваших же денег!",
            f"🌪️ {attacker.name} запутал(а) все ваши мысли!",
            f"🌪️ От {attacker.opponent.name} пахнет пылью и хаосом!"
        ],
        'МЕТЕОР': [
            f"☄️ {attacker.name} сбросил(а) на вас космический мусор!",
            f"☄️ {attacker.name} устроил(а) звездопад по голове!",
            f"☄️ {attacker.name} запустил(а) в вас Звезду Смерти",
            f"☄️ От {attacker.opponent.name} пахнет метеоритной пылью!"
        ],
        'ЛАВИНА': [
            f"🏔️ {attacker.name} засыпал(а) вас снежинками!",
            f"🏔️ {attacker.name} устроил(а) зимние игры в июле!",
            f"🏔️ От {attacker.opponent.name} пахнет мятным леденцом и холодком!"
        ],
        'ЦИКЛОН': [
            f"🌀 {attacker.name} запустил(а) вас в центрифугу!",
            f"🌀 {attacker.name} устроил(а) карусель из ваших мозгов!",
            f"🌀 От {attacker.opponent.name} пахнет вертолетом и тошнотой!"
        ],
        'НАПАЛМ': [
            f"💥 {attacker.name} устроил(а) вам вьетнамские джунгли!",
            f"💥 {attacker.name} поджарил(а) вас со всех сторон!",
            f"💥 От {attacker.opponent.name} пахнет бензином и приключениями!"
        ],
        'ЗЕМЛЕТРЯСЕНИЕ': [
            f"🏚️ {attacker.name} потанцевал(а) на вашем полу!",
            f"🏚️ {attacker.name} устроил(а) тест на сейсмоустойчивость!",
            f"🏚️ От {attacker.opponent.name} пахнет пылью и ремонтом!"
        ],
        'ВЕЛИКАЯ КВИНТЭССЕНЦИЯ': [
            f"🌈 {attacker.name} устроил(а) магический фейерверк!",
            f"🌈 {attacker.name} показал(а) вам все цвета радуги!",
            f"🌈 От {attacker.opponent.name} пахнет волшебством и нафталином!"
        ]
    }

    spell = ""
    combinations = load_combinations()
    for combination in combinations.items():
        if combination[1] == sorted(elements_used):
            spell = combination[0]

    if spell in spell_messages:
        print(f"{Style.BRIGHT}{random.choice(spell_messages[spell])}{reset}")


def show_end_game_message(loser, new_points):
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