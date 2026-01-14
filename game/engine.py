from utils.rules import show_rules
from ui.display import show_player_state
import time


class GameEngine:
    def __init__(self, player1, player2, deck, combinations_data, roman_data, colors):
        self.player1 = player1
        self.player2 = player2
        self.deck = deck
        self.whose_turn = 1  # 1 — player1, 0 — player2
        self.moves_counter = 1
        self.running = True
        self.combinations = combinations_data
        self.roman = roman_data
        self.colors = colors

    def run(self):
        while self.running:
            current = self.player1 if self.whose_turn else self.player2
            other = self.player2 if self.whose_turn else self.player1

            defense_result = True
            if self.moves_counter > 1:
                defense_result = current.defend(self.moves_counter)

            status_result = current.update_status(
                is_defended=defense_result,
                deck=self.deck,
                moves_counter=self.moves_counter
            )

            if status_result["game_over"]:
                self.end_game(current)
                return

            if status_result["skip_turn"]:
                self.whose_turn = 1 - self.whose_turn
                self.moves_counter += 1
                continue

            show_player_state(current, self.moves_counter)

            go_next = self.play(current)
            if not go_next:
                break

            self.whose_turn = 1 - self.whose_turn
            self.moves_counter += 1


    def play(self, player):
        while True:
            action = input("\nАТАКА:\n").strip()

            if len(action.split()) == 0:  # Проверка, если введена пустая строка
                continue

            elif action == "\help":
                help()
                ok = input()
                show_player_state(player, self.moves_counter)
                continue

            elif action == "\\rules" or action == '322':
                show_rules()
                ok = input()
                show_player_state(player, self.moves_counter)
                continue

            elif action == "\deck":
                print(self.deck.deck)
                print(f"КОЛ-ВО КАРТ: {len(self.deck.deck)}")
                ok = input()
                continue

            elif action == '\end' or action == '0':
                print("\nХОД ОКОНЧЕН")
                print("\n{:-^320}".format(""))
                player.last_move = []
                time.sleep(3)
                return True

            elif action == "\qqq":
                print("\n{:->20}".format(f" КОНЕЦ ИГРЫ ") + "{:-<300}\n".format(""))
                return False

            elif all(map(lambda i: i.isdigit(), action.split())):
                try:
                    success = player.make_move(action, self.deck, self.moves_counter)
                    if success:
                        while True:
                            action = input("\n")
                            if action == "\help":
                                help()
                                ok = input()
                                show_player_state(player, self.moves_counter)
                                continue
                            elif action == "\deck":
                                print(self.deck.deck)
                                print(f"КОЛ-ВО КАРТ: {len(self.deck.deck)}")
                                ok = input()
                                continue
                            elif action == '\end' or action == '0':
                                print("\nХОД ОКОНЧЕН")
                                print("\n{:-^320}".format(""))
                                time.sleep(3)
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


    def end_game(self, loser):
        try:
            from utils.data_loader import load_scoreboard, load_to_scoreboard
            import pandas as pd
            from ui.display import show_end_game_message
            data = load_scoreboard()
            new_points = 25 + (3 - self.moves_counter // 10) + (loser.opponent.hp // 10) + (
                        loser.opponent.spells_counter // 5)

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
            load_to_scoreboard(data)

            # ... вывод сообщений ...
            show_end_game_message(loser, new_points)

        except Exception as e:
            print(f"Ошибка при обновлении статистики: {e}")

        return False