import _thread
import random
import time

import vk_api
from data import token_id, group_id
from keyboards import *
from messages_rus import *
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from word_bank import words_easy, words_medium, words_hard

from hatbot.decorators import admin_required


class Bot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=token_id)
        self.long_poll = VkBotLongPoll(self.vk_session, group_id)
        self.vk = self.vk_session.get_api()

        self.func_dict = {  # словарь функций - что вызывать в ответ на команды игрока
            msg_begin: self.begin_game,
            msg_join: self.join_session,
            msg_leave: self.leave_game,
            msg_done: self.done_pass_check,
            msg_pass: self.done_pass_check,
            msg_results: self.results,
            msg_settings: self.start_settings,
            msg_random_hat: self.random_hat,
            msg_current_hat: self.current_hat,
            msg_custom_hat: self.custom_hat,
            msg_change_easy: self.input_change,
            msg_change_medium: self.input_change,
            msg_change_difficult: self.input_change,
            msg_stop_settings: self.stop_settings,
            msg_null_results: self.null_results,
            msg_queue: self.queue_turn,
        }

        self.event = None
        # информация о происходящем событии
        self.player_id = None
        # id игрока

        self.sessions = {}
        # для каждого ключа, кода сессии, значение - массив из 5 полей
        # нулевое поле - массив игроков, участвующих в игре
        #       нулевой игрок - администратор
        # первое поле - массив слов, которые лежат в шляпе
        # второе поле - массив из четырех элементов, -1 - если сейчас ожидается ввод числа слов такого типа:
        #       нулевое поле - начальное количество легких слов
        #       первое поле - начальное количество средних слов
        #       второе поле - начальное количество сложных слов
        # третье поле - идет ли сейчас ход, 0 - не идет, 1 - идет
        # четвертое поле - id следующего игрока в очереди

        self.players = {}
        # Для каждого ключа, id игрока, значение - массив из 4 полей
        # нулевое поле - в какой сессии участвует игрок
        # первое поле - массив флагов:
        #       нулевое поле - последняя клавиатура, чтобы вызывать при msg_wtf
        #       первое поле - флаг времени игрока, если оно 0 - значит не прошло, а если 1 - слова выдаваться не будут
        #       второе поле - последнее слово - чтобо возвращать в шляпу, если не угадать
        #       третье поле - флаг пишущего game code игрока: 0 - не пишет, 1 - сейчас должен написать
        #       четвертое поле - уникальный код хода
        #       пятое поле - количество очков игрока
        #       шестое поле - является ли администртором сессии: 0 - нет, 1 - да
        # второе поле - имя игрока
        # третье поле - peer_id игрока

    def msg_send(self, message, keyboard=None, peer=None):  # отправление сообщения
        if peer is None:
            peer = self.event.obj.peer_id
        self.vk.messages.send(
            peer_id=peer,
            random_id=get_random_id(),
            message=message,
            keyboard=keyboard
        )
        if self.player_id in self.players:
            self.players[self.player_id][1][0] = keyboard

    def null_flag(self):  # обнуляем флаги игрока, дйствующие при ходе
        self.players[self.player_id][1][1] = 0
        self.players[self.player_id][1][2] = None
        self.players[self.player_id][1][3] = 0
        self.players[self.player_id][1][4] = -1
        self.sessions[self.players[self.player_id][0]][3] = 0  # показываем что ход закончен

    def del_player(self):  # удаляем игрока
        self.players.pop(self.player_id)

    def end_turn(self):
        self.next_queue()
        self.null_flag()
        peer = self.players[self.sessions[self.players[self.player_id][0]][4]][3]
        self.return_lobby(msg_end_turn)
        self.msg_send(msg_next, peer=peer)

    def null_results(self):
        if self.players[self.player_id][1][6] == 1:
            player_session = self.sessions[self.players[self.player_id][0]]
            for player in player_session[0]:
                self.players[player][1][5] = 0
            self.msg_send(msg_null_results_done, settings_keyboard)
        else:
            self.msg_send(msg_not_admin, lobby_keyboard)

    def begin_game(self):  # начальный экран
        self.leave_session()  # уходим из сессии если игрок в ней состоит
        self.players[self.player_id] = [None, [None, 0, None, 1, -1, 0, 0], '', self.event.obj.peer_id]
        user_information = self.vk.users.get(user_ids=self.player_id)[0]
        user_name = user_information['first_name'] + ' ' + user_information['last_name']
        self.players[self.player_id][2] = user_name  # регистрация игрока и ставим флаг, что ждем game code
        self.msg_send(msg_begin_response)

    def next_queue(self):
        player = self.players[self.player_id]
        i = self.sessions[player[0]][0].index(self.player_id)
        self.sessions[player[0]][4] = self.sessions[player[0]][0][(i + 1) % len(self.sessions[player[0]][0])]
        print(self.sessions[player[0]][4], i, (i + 1) % len(self.sessions[player[0]][0]))

    def leave_session(self):  # выход игрока из сессии
        if self.player_id in self.players:
            player = self.players[self.player_id]
            if player[0] is not None:  # если игрок состоит в какой-то сессии
                player_session = self.sessions[player[0]]  # узнаем сессию игрока и удаляем его из players
                if player_session[4] == self.player_id:  # если он следующий, то берем следующего
                    self.next_queue()
                    peer = self.players[player_session[4]][3]
                    self.msg_send(msg_next, peer=peer)
                    if player[1][4] != -1:
                        player_session[3] = 0
                player_session[0].remove(self.player_id)  # удаляем игрока из массива участников сессии
                if len(player_session[0]) == 0:  # если в сессии не осталось игроков, то удаляем и ее
                    self.sessions.pop(player[0])
                else:
                    self.players[player_session[0][0]][1][6] = 1  # передаем администраторские права
            self.del_player()  # удаляем игрока

    def join_session(self):  # вход в сессию или создание новой
        game_code = self.event.obj.text
        # self.leave_session()  # если был в других сессиях, то выходим из них

        if game_code in self.sessions:  # если сессия уже есть, то добавляем в нее игрока
            self.sessions[game_code][0].append(self.player_id)
            self.players[self.player_id][0] = game_code  # добавляем игрока в сессию
            self.msg_send(msg_join_response + game_code, lobby_keyboard)

        else:  # если ее нет, то создаем ее
            self.sessions[game_code] = [[self.player_id], [], [0, 0, 0], 0, self.player_id]
            print(self.player_id)
            self.players[self.player_id][0] = game_code  # добавляем игрока в сессию в качестве администратора
            self.players[self.player_id][1][6] = 1  # присваеваем игроку флаг администратора
            self.random_hat()  # создаем шляпу случайным образом
            self.msg_send(msg_join_response_admin + game_code, admin_lobby_keyboard)

    def return_lobby(self, message):  # возвращает игрока в лобби
        if self.players[self.player_id][1][6] == 1:
            self.msg_send(message, admin_lobby_keyboard)
        else:
            self.msg_send(message, lobby_keyboard)

    def start_game(self):  # начало ход
        player_id = self.player_id
        if self.sessions[self.players[player_id][0]][3] == 0 and \
                self.sessions[self.players[player_id][0]][4] == self.player_id:  # начинаем ход, только если он не идет
            self.sessions[self.players[player_id][0]][3] = 1  # меняем флаг, что в сессии идет ход
            self.players[player_id][1][4] = random.random()  # создаем рандомный код этого хода
            this_turn = self.players[player_id][1][4]
            self.give_word()  # даем ему слово
            time.sleep(20)  # ждем 20 секунд, в это время могут приходить новые слова, на которые игрок отвечает
            if player_id in self.players and \
                    this_turn == self.players[player_id][1][4]:  # если игрок не закончил тот ход, то продолжаем
                self.players[player_id][1][1] = 1  # у игрока Время - теперь он не будет получать слова
                self.msg_send(msg_time, game_keyboard, self.players[player_id][3])
                time.sleep(3)  # ждем 3 секунды
                if player_id in self.players and this_turn == self.players[player_id][1][4]:
                    # опять же, если не закончил еще тот ход, то продолжаем
                    self.msg_send(msg_stop, game_keyboard, self.players[player_id][3])
        else:
            self.return_lobby(msg_turn_going)

    def give_word(self):  # функция выдачи игроку слова
        words_remaining = self.sessions[self.players[self.player_id][0]][1]  # массив оставшихся слов
        if len(words_remaining) > 0:  # если еще остались слова
            i_word = random.randint(0, len(words_remaining) - 1)
            new_word = words_remaining[i_word]  # выбираем случайное слово
            del words_remaining[i_word]  # удаляем это слово из шляпы
            self.players[self.player_id][1][2] = new_word  # записываем последнее выданное слово
            self.msg_send(new_word, game_keyboard)
        else:  # если слов не осталось
            self.end_turn()

    def done_word(self):  # функция угадывания слова
        self.players[self.player_id][1][5] += 1  # увеличиваем счет игрока
        if self.players[self.player_id][1][1] == 0:  # если время еще есть, то даем еще одно слово
            self.give_word()
        else:  # если время закончилось, то отправляем в лобби
            self.end_turn()

    def pass_word(self):  # функция заканчивания хода
        last_word = self.players[self.player_id][1][2]  # берем последнее слово игрока
        if last_word is not None:  # если оно было
            self.sessions[self.players[self.player_id][0]][1].append(last_word)  # возвращаем слово в шляпу
        self.end_turn()

    def done_pass_check(self):  # функция проверки условий на done/pass
        if self.players[self.player_id][1][4] != -1:  # только если идет ход
            if self.event.obj.text == msg_done:  # смотрим что именно
                self.done_word()
            else:
                self.pass_word()
        else:  # нужно начать ход
            self.return_lobby(msg_need_start)

    def leave_game(self):  # выход из игры
        self.leave_session()  # выходим из сессии
        self.msg_send(msg_leave_response)

    def results(self):
        player_session = self.sessions[self.players[self.player_id][0]]
        player_results = ''
        for i in range(len(player_session[0])):
            player_id_in_session = player_session[0][i]
            player_points = str(self.players[player_id_in_session][1][5])
            player_results += (self.players[player_id_in_session][2] + ': ' + player_points + '\n')
            # пишем на каждой строчке - имя и количество очков каждого игрока из сессии
        self.return_lobby(player_results)

    def queue_turn(self):
        player_session = self.sessions[self.players[self.player_id][0]]
        player_queue = ''
        for i in range(len(player_session[0])):
            player_id_in_session = player_session[0][i]
            if player_session[4] == player_id_in_session:
                player_queue += '  ->'
            player_queue += (self.players[player_id_in_session][2] + '\n')
            # пишем на каждой строчке - имя каждого игрока из сессии
        self.return_lobby(player_queue)

    @admin_required
    def start_settings(self):  # функция настроек, доступная только администратору
        self.msg_send(msg_start_settings, settings_keyboard)

    @admin_required
    def stop_settings(self):  # завершение настроек шляпы
        self.msg_send(msg_custom_hat_created, admin_lobby_keyboard)

    @admin_required
    def custom_hat(self):  # создаем индивидуальную шляпу
        player_session = self.sessions[self.players[self.player_id][0]]
        number_words = msg_number_easy + str(player_session[2][0]) + \
            ', ' + msg_number_medium + str(player_session[2][1]) + ', ' + \
            msg_number_difficult + str(player_session[2][2])
        self.msg_send(number_words, customizing_keyboard)

    def make_custom_change(self, words_numb):
        player_session = self.sessions[self.players[self.player_id][0]]
        index_flag = player_session[2].index(-1)
        player_session[2][index_flag] = words_numb
        self.put_words()
        number_words = msg_number_easy + str(player_session[2][0]) + \
            ', ' + msg_number_medium + str(player_session[2][1]) + ', ' + \
            msg_number_difficult + str(player_session[2][2])
        self.msg_send(number_words, customizing_keyboard)

    def input_rank(self, rank):
        player_session = self.sessions[self.players[self.player_id][0]]
        # проверяем, завершил ли игрок предыдущий ввод
        if -1 not in player_session[2]:
            player_session[2][rank] = -1
            self.msg_send(msg_input[rank])
        else:
            self.msg_send(msg_input_going)

    @admin_required
    def input_change(self):
        rank = self.event.obj.text
        if rank == msg_change_easy:
            i = 0
        elif rank == msg_change_medium:
            i = 1
        elif rank == msg_change_difficult:
            i = 2
        else:
            return
        self.input_rank(i)

    def put_words(self):
        player_session = self.sessions[self.players[self.player_id][0]]
        player_session[1] = []
        player_session[1] += random.sample(words_easy, k=player_session[2][0])
        player_session[1] += random.sample(words_medium, k=player_session[2][1])
        player_session[1] += random.sample(words_hard, k=player_session[2][2])

    @admin_required
    def current_hat(self):  # игра продолжается с текущей шляпой
        self.msg_send(msg_current_hat_played, admin_lobby_keyboard)

    @admin_required
    def random_hat(self):  # создается шляпа по умолчанию
        player_session = self.sessions[self.players[self.player_id][0]]
        player_session[2] = [100, 100, 100]
        self.put_words()
        self.msg_send(msg_random_hat_created, admin_lobby_keyboard)  # возвращаем адмнистратора в админ. лобби

    def input_numb(self):
        if self.event.obj.text.isdigit():  # ввели число
            if int(self.event.obj.text) > 1000:  # проверим, не очень ли большое число ввели
                self.msg_send(msg_too_big_int)
                self.make_custom_change(1000)
            else:
                self.make_custom_change(int(self.event.obj.text))
        else:  # если ввел не число, говорим, что надо ввести число
            self.msg_send(msg_not_int)

    def bot_respond(self):  # функция проверки всех событий
        for temp_event in self.long_poll.listen():
            # print(self.players)
            # print(self.sessions)
            if temp_event.type == VkBotEventType.MESSAGE_NEW:  # смотрим все новые сообщения
                self.event = temp_event
                self.player_id = self.event.obj.from_id
                if self.event.obj.text == msg_begin:
                    self.begin_game()
                elif self.player_id in self.players:
                    if self.players[self.player_id][0] is not None:
                        if -1 in self.sessions[self.players[self.player_id][0]][2]\
                                and self.players[self.player_id][1][6] == 1:
                            self.input_numb()
                        elif self.event.obj.text in self.func_dict:
                            self.func_dict[self.event.obj.text]()
                        elif self.event.obj.text == msg_start:  # если старт - то запускаем на поток, чтобы время шло
                            _thread.start_new_thread(self.start_game, ())
                        else:
                            self.msg_send(msg_wtf, keyboard=self.players[self.player_id][1][0])
                    elif self.players[self.player_id][1][3] == 1 \
                            and len(self.event.obj.text) < 10:  # условие того, что нам присылают код
                        self.func_dict[msg_join]()
                    else:
                        self.msg_send(msg_need_join, begin_keyboard)
                else:
                    self.msg_send(msg_need_begin, begin_keyboard)
