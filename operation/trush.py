import common
import time
import urllib.request
import json
import random
import signal
import numpy as np
import math
from collections import deque
from keras.models import Input, Model, load_model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape, Permute
from keras.layers.convolutional import Conv2D, Conv2DTranspose, Convolution2D, MaxPooling2D, Cropping2D, Deconvolution2D
from keras.layers.merge import concatenate, add
from keras.optimizers import Adam
from keras.utils import plot_model
import matplotlib.pyplot as plt
import sys
from tensorflow.python.client import device_lib


def get_game_team_id():
    global TEAM_ID
    url = BASE_URL + "matches"
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        for match in response:
            if match["id"] == MATCH_ID:
                TEAM_ID = match["teamID"]


def get_game_set(team_id):
    global HEIGHT, WIDTH, START_UNIX_TIME, AGENTS, ENEMY_AGENTS, NUMBER_OF_AGENTS
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        HEIGHT = response["height"]
        WIDTH = response["width"]
        START_UNIX_TIME = response["startedAtUnixTime"]
        for team_info in response["teams"]:
            agents = []
            if team_info["teamID"] == team_id:
                for i in team_info["agents"]:
                    agents.append(i["agentID"])
                AGENTS = agents
            else:
                for i in team_info["agents"]:
                    agents.append(i["agentID"])
                ENEMY_AGENTS = agents
        NUMBER_OF_AGENTS = len(agents)


def get_game_status(team_id):
    status = np.zeros([HEIGHT, WIDTH])
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        y = 0
        for y_tiled in response["tiled"]:
            x = 0
            for x_tiled in y_tiled:
                if x_tiled == 0:
                    status[y][x] = 0
                elif y_tiled == team_id:
                    status[y][x] = 1
                else:
                    status[y][x] = 2
                x += 1
            y += 1
        return status


def get_game_coordinate(team_id):
    status = []
    for i in range(NUMBER_OF_AGENTS * 2):
        status.append(np.zeros([HEIGHT, WIDTH]))
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        teams = response["teams"]
        for one in teams:
            plus = 0
            if one["teamID"] != team_id:
                plus = 1
            for i, agent in enumerate(one["agents"]):
                x = agent["x"]
                y = agent["y"]
                status[plus * NUMBER_OF_AGENTS + i][y -
                                                    1][x - 1] = (1 if plus == 0 else -1)
        status = np.array(status)
        return status


def get_panel_score():
    status = np.zeros([HEIGHT, WIDTH])
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        y = 0
        for y_tiled in response["points"]:
            x = 0
            for x_tiled in y_tiled:
                status[y][x] = x_tiled
                x += 1
            y += 1
    return status


def post_agent_action(agent_id, move_coordinate, move_types):
    url = BASE_URL + "matches/" + str(MATCH_ID) + "/action"
    method = "POST"
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    actions = []
    for (agent, coordinate, move_type) in zip(agent_id, move_coordinate, move_types):
        # print(coordinate)
        actions.append({
            "agentID": agent,
            "dx": coordinate[0],
            "dy": coordinate[1],
            "type": move_type
        })

    json_object = {"actions": actions}
    json_data = json.dumps(json_object).encode("utf-8")
    # print(json_data)

    request = urllib.request.Request(
        url, data=json_data, method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        request_body = response.read().decode("utf-8")
    # print(request_body)


def test_move(arg1, arg2):
    global turn
    if turn >= 101:
        return

    coo = []
    for j in range(6):
        coo.append(set_list[random.randrange(8)])
    print(turn)
    turn += 1
    post_agent_action([1, 2, 3, 4, 5, 6], coo, [
                      "move", "move", "move", "move", "move", "move"])


class Memory:
    def __init__(self):
        self.accumulate = deque(maxlen=1000)

    def add(self, experience):
        self.accumulate.append(experience)

    def data(self, batch_size):
        index = np.random.choice(
            np.arange(len(self.accumulate)), size=batch_size, replace=False)
        return [self.accumulate[i] for i in index]

    def len(self):
        return len(self.accumulate)


def create_Qmodel():
    learning_rate = 0.1**(3)
    game_input = Input(shape=(HEIGHT, WIDTH, 3), name="game_net")

    x_direct = Conv2D(filters=1, kernel_size=(1, WIDTH), strides=(
        1, 1), activation="relu", padding="valid")(game_input)
    x_direct = Flatten()(x_direct)

    y_direct = Conv2D(filters=1, kernel_size=(HEIGHT, 1), strides=(
        1, 1), activation="relu", padding="valid")(game_input)
    y_direct = Flatten()(y_direct)

    game_field = Input(shape=(HEIGHT, WIDTH), name="game_field")
    panel = Flatten()(game_field)

    surround = Conv2D(filters=16, kernel_size=(3, 3), strides=(
        1, 1), activation="relu", padding="same")(game_input)
    surround = Conv2D(filters=16, kernel_size=(3, 3), strides=(
        1, 1), activation="relu", padding="same")(surround)
    surround = MaxPooling2D()(surround)
    surround = Conv2D(filters=32, kernel_size=(3, 3), strides=(
        1, 1), activation="relu", padding="same")(surround)
    surround = Conv2D(filters=32, kernel_size=(3, 3), strides=(
        1, 1), activation="relu", padding="same")(surround)
    surround = MaxPooling2D()(surround)
    surround = Flatten()(surround)

    intput_cooridnate = []
    for i in range(NUMBER_OF_AGENTS * 2):
        intput_cooridnate.append(Input(shape=(HEIGHT, WIDTH)))

    finish = [x_direct, y_direct, panel, surround]
    for coordinate in intput_cooridnate:
        coordinate = Flatten()(coordinate)
        finish.append(coordinate)

    final = concatenate(finish, axis=1)
    final = Dense(HEIGHT * WIDTH * 15, activation="relu")(final)
    final = Dense(HEIGHT * WIDTH * 6, activation="relu")(final)
    output = []
    for i in range(NUMBER_OF_AGENTS):
        output.append(Dense(17, activation="linear",
                            name="output" + str(i))(final))
    optimizer = Adam(learning_rate=learning_rate)
    model_inputs = [game_input, game_field]
    for coordinate in intput_cooridnate:
        model_inputs.append(coordinate)
    model = Model(inputs=model_inputs, outputs=output)
    model.compile(optimizer=optimizer, loss='mean_squared_error')
    plot_model(model, to_file="height" + str(HEIGHT) + "width" + str(WIDTH) +
               "agents" + str(NUMBER_OF_AGENTS) + ".png", show_shapes=True)

    return model


def game_status_batch(game_input):
    return game_input.reshape((1, HEIGHT, WIDTH, 3))


def game_field_batch(game_field):
    return game_field.reshape((1, HEIGHT, WIDTH))


def status_binary(game_input):
    index = game_input
    temp = np.zeros([HEIGHT, WIDTH, 3])

    for i in range(0, HEIGHT):
        for j in range(0, WIDTH):
            temp[i, j, int(index[i, j])] = 1
    return temp


def get_action(game_status, game_input, model, turn, agent_coordinate):
    p = 0.1**(3) + 0.9 / (1.0 + turn)
    status = status_binary(game_status)
    sent_data = []
    sent_data.append(game_status_batch(status))
    sent_data.append(game_field_batch(game_input))
    for coordinate in agent_coordinate:
        sent_data.append(game_field_batch(coordinate))
    # sent_data = np.array(sent_data)
    result = model.predict(sent_data)
    next_action = []
    # print(game_field_batch(game_input))
    if p <= np.random.uniform(0, 1):
        for agent in result:
            # print(agent[0])
            next_action.append(np.argmax(agent[0]))
    else:
        for agent in result:
            next_action.append(np.random.randint(0, 8))

    return next_action, result


def learning(main_model, memory, gamma, target_model):
    main_input = np.zeros((BATCH_SIZE, HEIGHT, WIDTH, 3))
    sub_input = np.zeros((BATCH_SIZE, HEIGHT, WIDTH))
    coordinate_input = []
    for i in range(NUMBER_OF_AGENTS * 2):
        coordinate_input.append(np.zeros((BATCH_SIZE, HEIGHT, WIDTH)))
    mini_batch = memory.data(BATCH_SIZE)
    targets = []
    for i in range(NUMBER_OF_AGENTS):
        targets.append(np.zeros((BATCH_SIZE, 17)))

    for i, (now_status, points_status, next_status, action, reward, now_coordinate, next_coordinate) in enumerate(mini_batch):
        now_status = status_binary(now_status)
        main_input[i: i + 1] = now_status
        sub_input[i: i + 1] = points_status
        # print(main_input)
        # print(game_field_batch(points_status))

        target = []
        next_status = status_binary(next_status)
        next_batch = game_status_batch(next_status)

        sent_data = [next_batch, game_field_batch(points_status)]
        for coordinate in now_coordinate:
            sent_data.append(game_field_batch(coordinate))

        predict_main = main_model.predict(sent_data)
        next_action = []
        for one in predict_main:
            next_action.append(np.argmax(one[0]))
        sent_data = [game_status_batch(
            next_status), game_field_batch(points_status)]
        for coordinate in next_coordinate:
            sent_data.append(game_field_batch(coordinate))
        predict_main = main_model.predict(sent_data)
        for (j, one) in zip(next_action, predict_main):
            # print(one[0][j])
            target.append(reward + gamma * one[0][j])
            # print(target)

        target_data = [game_status_batch(
            now_status), game_field_batch(points_status)]
        for coordinate in now_coordinate:
            target_data.append(game_field_batch(coordinate))

        target_predict = main_model.predict(target_data)
        # print(target_predict)

        for (j, target_temp) in zip(range(NUMBER_OF_AGENTS), target_predict):
            for (k, point) in zip(range(17), target_temp[0]):
                targets[j][i][k] = point

        for j in range(NUMBER_OF_AGENTS):
            # print(target[j])
            targets[j][i][action[j]] = target[j]
    # print(targets)
    fit_data = [main_input, sub_input]
    for j, coordinate in enumerate(now_coordinate):
        coordinate_input[j][i: i + 1] = coordinate
        fit_data.append(coordinate_input[j])
    # print(fit_data)
    main_model.fit(fit_data, targets, epochs=1, verbose=0)

    return main_model


before_my_score = 0
before_my_area = 0
before_my_tile = 0
before_enemy_score = 0
before_enemy_area = 0
before_enemy_tile = 0


def get_reward(team_id):
    global before_my_score, before_my_area, before_my_tile, before_enemy_score, before_enemy_area, before_enemy_tile
    next_status = get_game_status(team_id)
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        my_score = 0
        my_area = 0
        my_tile = 0
        enemy_score = 0
        enemy_area = 0
        enemy_tile = 0
        for team_info in response["teams"]:
            if team_info["teamID"] == team_id:
                my_area = team_info["areaPoint"]
                my_tile = team_info["tilePoint"]
                my_score = my_area + my_tile
            else:
                enemy_area = team_info["areaPoint"]
                enemy_tile = team_info["tilePoint"]
                enemy_score = enemy_area + enemy_tile
        reward = (my_score - before_my_score) / 100
        if before_enemy_score - enemy_score > 0:
            reward += (before_enemy_score - enemy_score) / 100
        before_my_score = my_score
        before_my_area = my_area
        before_my_tile = my_tile
        before_enemy_score = enemy_score
        before_enemy_area = enemy_area
        before_enemy_tile = enemy_tile
        # print(response["turn"])
        return next_status, reward


# Move number
UPWARD = [0, -1]
UPPER_RIGHT = [1, -1]
RIGHT = [1, 0]
LOWER_RIGHT = [1, 1]
UNDER = [0, 1]
LOWER_LEFT = [-1, 1]
LEFT = [-1, 0]
UPPER_LEFT = [-1, -1]
STAY = [0, 0]
ACTION = ["move", "remove", "stay"]
AGENTS = []
ENEMY_AGENTS = []

SET_LIST = [UPWARD, UPPER_RIGHT, RIGHT, LOWER_RIGHT,
            UNDER, LOWER_LEFT, LEFT, UPPER_LEFT]

BASE_URL = "http://localhost:8081/"
TOKEN = "TEMP_TOKEN"
MATCH_ID = 1
TEAM_ID = 2
HEIGHT = 10
WIDTH = 10
NUMBER_OF_AGENTS = 3

START_UNIX_TIME = 0
interval_millisecond = 50
turn_millisecond = 35
PREPARATION_SECOND = 2
MAX_TURN = 30

# parameter
BATCH_SIZE = 10
LEARNING_NUMBER = 2000
PRODUCTION = False
DISCOUNT = 0.95

DQN_MODE = True

reward_list = np.zeros(LEARNING_NUMBER + 1)


def exit_signal(sig, fram):
    main_model.save("hello.h5")
    plt.plot(reward_list)
    plt.show()
    sys.exit(1)


if __name__ == '__main__':
    main_model = create_Qmodel()
    target_model = create_Qmodel()
    memory = Memory()
    signal.signal(signal.SIGINT, exit_signal)
    if not PRODUCTION:
        # start learning
        for episode in range(LEARNING_NUMBER + 1):
            if episode == 1:
                interval_millisecond = 3000
                turn_millisecond = 500
            else:
                interval_millisecond = 80 + math.floor(episode / 75)
                turn_millisecond = 80 + math.floor(episode / 75)
            server = common.gamebord_exec(interval_millisecond, turn_millisecond, MAX_TURN, PREPARATION_SECOND,
                                          "/home/jellyfish/procon30/simulator/build/public-field/A-3.json")
            server.start()
            get_game_team_id()
            get_game_set(TEAM_ID)
            episode_reward = 0
            target_model = main_model

            # prepare
            while True:
                if time.time() >= START_UNIX_TIME:
                    break
            get_reward(TEAM_ID)
            start_time = time.perf_counter()
            for t in range(MAX_TURN):
                # print(t)
                step = False
                finish = False
                # init
                reward = 0
                next_status = 0
                status = 0
                panel = 0
                next_status = 0
                next_coordinate = 0
                while True:
                    end_time = time.perf_counter()
                    elapsed_time = (end_time - start_time) * 1000 - \
                        (t * (interval_millisecond + turn_millisecond))
                    if not step:
                        status = get_game_status(TEAM_ID)
                        # print(status)
                        now_coordinate = get_game_coordinate(TEAM_ID)
                        panel = get_panel_score()
                        action, test = get_action(
                            status, panel, main_model, episode, now_coordinate)
                        # print(action)
                        # my_agent
                        move = []
                        types = []
                        for i in action:
                            if i == 16:
                                move.append([0, 0])
                                types.append(ACTION[2])
                            else:
                                move.append(SET_LIST[(i % 8)])
                                types.append(ACTION[math.floor(i / 8)])
                        post_agent_action(AGENTS, move, types)

                        # enemy_agent
                        enemy_status = get_game_status(1)
                        enemy_action, enemy_test = get_action(
                            enemy_status, panel, main_model, 10**10, get_game_coordinate(1))
                        enemy_move = []
                        enemy_types = []
                        for i in action:
                            if i == 16:
                                enemy_move.append([0, 0])
                                enemy_types.append(ACTION[2])
                            else:
                                enemy_move.append(SET_LIST[(i % 8)])
                                enemy_types.append(ACTION[math.floor(i / 8)])
                        post_agent_action(
                            ENEMY_AGENTS, enemy_move, enemy_types)

                        step = True
                    if elapsed_time >= turn_millisecond + interval_millisecond:
                        break
                    elif elapsed_time >= turn_millisecond and not finish:
                        next_status, reward = get_reward(TEAM_ID)
                        next_coordinate = get_game_coordinate(TEAM_ID)
                        finish = True
                if t + 1 == MAX_TURN:
                    if before_my_score > before_enemy_score:
                        reward += 0
                episode_reward += reward
                if episode == 0:
                    continue
                memory.add((status, panel, next_status, action,
                            reward, now_coordinate, next_coordinate))

                # print(memory.len())
                if memory.len() > BATCH_SIZE:
                    main_model = learning(
                        main_model, memory, DISCOUNT, target_model)

                if DQN_MODE:
                    target_model = main_model

                if t + 1 == MAX_TURN:
                    print("episode:" + str(episode) +
                          " rewards:" + str(episode_reward))
                    reward_list[episode] = episode_reward
                    break
            server.end()
    main_model.save("hello.h5")
    plt.plot(reward_list)
    plt.show()
