import common
import time
import urllib.request
import json
import random
import signal
import numpy as np
import math
import os
from keras.models import Input, Model, load_model
from keras.layers.core import Dense, Flatten
from keras.layers.merge import concatenate
from keras.optimizers import Adam
import matplotlib.pyplot as plt
import sys


def get_game_team_id():
    global TEAM_ID, interval_millisecond, turn_millisecond, MAX_TURN
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
                interval_millisecond = match["intervalMillis"]
                turn_millisecond = match["turnMillis"]
                MAX_TURN = match["turns"]


def get_game_set(team_id):
    global HEIGHT, WIDTH, START_UNIX_TIME, AGENTS, ENEMY_AGENTS, NUMBER_OF_AGENTS
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    try:
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
    except urllib.error.HTTPError as e:
        response = e.read()
        response = json.loads(response)
        START_UNIX_TIME = response["startAtUnixTime"]


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
        for y, y_tiled in enumerate(response["tiled"]):
            for x, x_tiled in enumerate(y_tiled):
                if x_tiled == 0:
                    status[y][x] = 0
                elif x_tiled == team_id:
                    status[y][x] = 1
                else:
                    status[y][x] = -1
        return status


def get_my_coordinate(team_id, agent_id):
    status = np.zeros((HEIGHT, WIDTH))
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
            if one["teamID"] == team_id:
                for agent in one["agents"]:
                    x = agent["x"]
                    y = agent["y"]
                    status[y - 1][x - 1] = (2 if agent["agentID"] == agent_id else 1)
        return status


def get_agent_coordinate(team_id, agent_id):
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
            if one["teamID"] == team_id:
                for agent in one["agents"]:
                    if agent["agentID"] == agent_id:
                        x = agent["x"]
                        y = agent["y"]
                        return x, y


def get_enemy_coordinate(team_id):
    status = np.zeros((HEIGHT, WIDTH))
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
            if one["teamID"] != team_id:
                for agent in one["agents"]:
                    x = agent["x"]
                    y = agent["y"]
                    status[y - 1][x - 1] = 3
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
        for y, y_tiled in enumerate(response["points"]):
            for x, x_tiled in enumerate(y_tiled):
                status[y][x] = x_tiled
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


def next_turn():
    global TEAM_ID
    url = BASE_URL + "next_step"
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        response = json.load(response)


def create_Qmodel():
    panel_input = Input(shape=(HEIGHT, WIDTH))
    panel_flattan = Flatten()(panel_input)
    status_input = Input(shape=(HEIGHT, WIDTH))
    status_flattan = Flatten()(status_input)
    my_agents = Input(shape=(HEIGHT, WIDTH))
    my_flattan = Flatten()(my_agents)
    enemy_agents = Input(shape=(HEIGHT, WIDTH))
    enemy_flattan = Flatten()(enemy_agents)
    action_input = Input(shape=(17,))
    # action_flattan = Flatten()(action_input)
    inputs_flattan = concatenate(
        [panel_flattan, status_flattan, my_flattan, enemy_flattan, action_input], axis=-1)
    out = Dense(HEIGHT * WIDTH * 10, activation="relu")(inputs_flattan)
    out = Dense(HEIGHT * WIDTH * 10, activation="relu")(out)
    out = Dense(1, activation="linear")(out)
    final = Model(inputs=[panel_input, status_input, my_agents,
                          enemy_agents, action_input], outputs=out)
    final.compile(optimizer=Adam(),
                  loss="mean_squared_error")

    return final


def action_check(field_input, status_input, my_input, action, agent_x, agent_y, my_panel_duplicate, minus):
    if action == 16:
        return False  # stay is break

    agent_x = agent_x + SET_LIST[action % 8][0]
    agent_y = agent_y + SET_LIST[action % 8][1]

    if agent_x <= 0 or agent_y <= 0 or agent_x > WIDTH or agent_y > HEIGHT:
        return False  # out of field

    if math.floor(action / 8) == 0 and status_input[agent_y - 1][agent_x - 1] == -1:
        return False

    if math.floor(action / 8) == 0 and status_input[agent_y - 1][agent_x - 1] == 1:
        return my_panel_duplicate

    if math.floor(action / 8) == 0 and field_input[agent_y - 1][agent_x - 1] < 0:
        return minus

    if math.floor(action / 8) == 1 and status_input[agent_y - 1][agent_x - 1] != -1:
        return False
    # print(str(agent_x) + " " + str(agent_y))

    return True


def get_action(model, panel_input, status_input, my_input, enemy_input, turn, rand, team_id, agent_id, other_agent_coordinate):
    # epsilon = 0.1**(3) + 0.9 / (1.0 + turn)
    set_coordinate = [0, 0]
    next_actions = []
    panel_non_reshape = panel_input
    panel_input = input_reshape(panel_input)
    status_non_reshape = status_input
    my_non_reshape = my_input
    status_input = input_reshape(status_input)
    my_input = input_reshape(my_input)
    enemy_input = input_reshape(enemy_input)
    set_actions = []
    agent_x, agent_y = get_agent_coordinate(team_id, agent_id)

    # normal
    for i in range(17):
        if not action_check(panel_non_reshape, status_non_reshape, my_non_reshape, i, agent_x, agent_y, False, False):
            continue
        set_actions.append(i)
        pattan = np.zeros((17,))
        pattan[i] = 1.0
        pattan = pattan_reshape(pattan)
        result = model.predict(
            [panel_input, status_input, my_input, enemy_input, pattan])
        next_actions.append(result)

    # print(str(agent_x) + " " + str(agent_y))
    if random.random() > rand and len(next_actions) >= 4:
        for i in range(len(next_actions)):
            action = np.argmax(next_actions)
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]
    elif len(next_actions) >= 4:
        for i in range(len(next_actions)):
            action = np.random.randint(0, len(set_actions))
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]

    # special and duplicate code -> Fix if I have a time.
    for i in range(17):
        if not action_check(panel_non_reshape, status_non_reshape, my_non_reshape, i, agent_x, agent_y, True, False):
            continue
        set_actions.append(i)
        pattan = np.zeros((17,))
        pattan[i] = 1.0
        pattan = pattan_reshape(pattan)
        result = model.predict(
            [panel_input, status_input, my_input, enemy_input, pattan])
        next_actions.append(result)

    # print(str(agent_x) + " " + str(agent_y))
    if random.random() > rand and len(next_actions) >= 4:
        for i in range(len(next_actions)):
            action = np.argmax(next_actions)
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]
    elif len(next_actions) >= 4:
        for i in range(len(next_actions)):
            action = np.random.randint(0, len(set_actions))
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]
    # special and duplicate code -> Fix if I have a time.
    for i in range(17):
        if not action_check(panel_non_reshape, status_non_reshape, my_non_reshape, i, agent_x, agent_y, True, True):
            continue
        set_actions.append(i)
        pattan = np.zeros((17,))
        pattan[i] = 1.0
        pattan = pattan_reshape(pattan)
        result = model.predict(
            [panel_input, status_input, my_input, enemy_input, pattan])
        next_actions.append(result)

    # print(str(agent_x) + " " + str(agent_y))
    if random.random() > rand:
        for i in range(len(next_actions)):
            action = np.argmax(next_actions)
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]
    else:
        for i in range(len(next_actions)):
            action = np.random.randint(0, len(set_actions))
            set_coordinate[0] = agent_x + SET_LIST[set_actions[action] % 8][0]
            set_coordinate[1] = agent_y + SET_LIST[set_actions[action] % 8][1]
            if not check_duplicate(set_coordinate, other_agent_coordinate):
                return set_actions[action], next_actions[action], set_coordinate
            else:
                del next_actions[action]
                del set_actions[action]
    # stay
    pattan = np.zeros((17,))
    pattan[16] = 1.0
    pattan = pattan_reshape(pattan)
    result = model.predict([panel_input, status_input, my_input, enemy_input, pattan])
    return 16, result, [agent_x, agent_y]


def check_duplicate(agent_coordinate, other_coordinate):
    for check in other_coordinate:
        if check == other_coordinate:
            return True
    return False


def get_reward(team_id):
    url = BASE_URL + "matches/" + str(MATCH_ID)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    request = urllib.request.Request(url, headers=headers)
    my_score = 0
    enemy_score = 0
    with urllib.request.urlopen(request) as response:
        response = json.load(response)
        for team in response["teams"]:
            if team["teamID"] == team_id:
                my_score = team["areaPoint"] + team["tilePoint"]
            else:
                enemy_score = team["areaPoint"] + team["tilePoint"]
    return my_score, enemy_score


def input_reshape(input_array):
    return input_array.reshape((1, HEIGHT, WIDTH))


def pattan_reshape(pattan_input):
    return pattan_input.reshape((1, 17))


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
PREPARATION_SECOND = 0
MAX_TURN = 30

# parameter
BATCH_SIZE = 10
LEARNING_NUMBER = 50
PRODUCTION = True
DISCOUNT = 0.95

DQN_MODE = True
now_turn = 0

myscore_list = np.zeros(LEARNING_NUMBER + 1)
enemyscore_list = np.zeros(LEARNING_NUMBER + 1)

basedir = "./data/"


def exit_signal(sig, fram):
    main_model.save(basedir + dirname + "/" + "model.h5")
    plt.plot(myscore_list)
    plt.plot(enemyscore_list)
    plt.savefig(basedir + dirname + "/" + "all-episode.png")
    sys.exit(1)


dirname = ""

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_signal)
    if not PRODUCTION:
        # start learning
        MAX_TURN = int(sys.argv[1])
        filepath = sys.argv[2]
        dirname = sys.argv[3]
        port = int(sys.argv[4])
        BASE_URL = "http://localhost:" + str(port) + "/"
        if not os.path.exists(basedir + dirname):
            os.mkdir(basedir + dirname)
            os.mkdir(basedir + dirname + "/episode")
        for episode in range(LEARNING_NUMBER):
            server = common.Gamebord_exec(interval_millisecond, turn_millisecond, MAX_TURN, PREPARATION_SECOND,
                                          filepath, port, "--notime")
            server.start()
            get_game_team_id()
            get_game_set(TEAM_ID)
            if episode == 0:
                main_model = create_Qmodel()
                enemy_modle = create_Qmodel()
            target_modle = main_model
            my_episode = []
            enemy_episode = []
            turn_episode = []
            for turn in range(MAX_TURN):
                my_player = []
                enemy_player = []
                panel_input = get_panel_score()
                status_input = get_game_status(TEAM_ID)
                before_my_reward, before_enemy_reward = get_reward(TEAM_ID)
                my_action = []
                my_coordinate = []
                my_type = []
                turn_episode.append(turn)
                for i in range(NUMBER_OF_AGENTS):
                    # print(i)
                    my_input = get_my_coordinate(TEAM_ID, AGENTS[i])
                    my_enemy_input = get_enemy_coordinate(TEAM_ID)
                    next_action, action_point, action_coordinate = get_action(
                        main_model, panel_input, status_input, my_input, my_enemy_input, turn, 0.3, TEAM_ID, AGENTS[i], my_coordinate)
                    my_coordinate.append(action_coordinate)
                    if next_action == 16:
                        my_action.append([0, 0])
                        my_type.append("stay")
                    else:
                        my_action.append(SET_LIST[next_action % 8])
                        my_type.append(ACTION[math.floor(next_action / 8)])
                    my_player.append(
                        (panel_input, status_input, my_input, my_enemy_input, next_action))
                post_agent_action(AGENTS, my_action, my_type)

                enemy_action = []
                enemy_type = []
                enemy_coordinate = []
                status_input = get_game_status(1)
                for i in range(NUMBER_OF_AGENTS):
                    enemy_input = get_my_coordinate(1, ENEMY_AGENTS[i])
                    enemy_enemy_input = get_enemy_coordinate(1)
                    next_action, action_point, action_coordinate = get_action(
                        main_model, panel_input, status_input, enemy_input, enemy_enemy_input, 10**10, 0.2, 1, ENEMY_AGENTS[i], action_coordinate)
                    enemy_coordinate.append(action_coordinate)
                    if next_action == 16:
                        enemy_action.append([0, 0])
                        enemy_type.append("stay")
                    else:
                        enemy_action.append(SET_LIST[next_action % 8])
                        enemy_type.append(ACTION[math.floor(next_action / 8)])
                    enemy_player.append(
                        (panel_input, status_input, enemy_input, enemy_enemy_input, next_action))
                post_agent_action(ENEMY_AGENTS, enemy_action, enemy_type)
                next_turn()
                myscore_list[episode], enemyscore_list[episode] = get_reward(
                    TEAM_ID)
                reward = (myscore_list[episode] - before_my_reward)
                if enemyscore_list[episode] - before_enemy_reward < 0:
                    reward += enemyscore_list[episode] - before_enemy_reward
                all_panel, all_status, all_my, all_enemy, all_next = [], [], [], [], []
                for panel, status, my, enemy, next_action in my_player:
                    all_panel.append(panel)
                    all_status.append(status)
                    all_my.append(my)
                    all_enemy.append(enemy)
                    action = np.zeros((17,))
                    action[next_action] = 1.0
                    all_next.append(action)
                # print(all_next)
                main_model.fit([all_panel, all_status, all_my, all_enemy, all_next], np.array(
                    [reward] * len(all_panel)), epochs=2, verbose=0)

                reward = (enemyscore_list[episode] - before_enemy_reward)
                if myscore_list[episode] - before_my_reward < 0:
                    reward += myscore_list[episode] - before_my_reward
                my_episode.append(myscore_list[episode])
                enemy_episode.append(enemyscore_list[episode])
            # enemy
                all_panel, all_status, all_my, all_enemy, all_next = [], [], [], [], []
                for panel, status, my, enemy, next_action in enemy_player:
                    all_panel.append(panel)
                    all_status.append(status)
                    all_my.append(my)
                    all_enemy.append(enemy)
                    action[next_action] = 1.0
                    all_next.append(action)
                main_model.fit([all_panel, all_status, all_my, all_enemy, all_next], np.array(
                    [reward] * len(all_panel)), epochs=2, verbose=0)
            plt.plot(turn_episode, my_episode, label='my')
            plt.plot(turn_episode, enemy_episode, label='enemy')
            plt.savefig(basedir + dirname + "/" + "episode/" + "episode-" + str(episode) + ".png")
            plt.clf()
            now_turn += 1
            server.end()
            # player
            print("episode:" + str(episode) + " my score:" + str(myscore_list[episode]) + " enemy score:" + str(enemyscore_list[episode]))
            NUMBER_OF_AGENTS = np.random.randint(2, 9)
            common.random_field(HEIGHT, WIDTH, NUMBER_OF_AGENTS, port)
            enemyscore_list[episode] *= -1
        main_model.save(basedir + dirname + "/" + "model.h5")
        plt.plot(myscore_list)
        plt.plot(enemyscore_list)
        plt.savefig(basedir + dirname + "/" + "all-episode.png")
    else:
        if sys.argv[1] == "local":
            MATCH_ID = 1
            TOKEN = ""
        else:
            MATCH_ID = int(sys.argv[1])
            with open("./token.txt") as f:
                TOKEN = f.read()
            BASE_URL = "http://10.10.52.252"
        get_game_team_id()
        get_game_set(TEAM_ID)
        main_model = create_Qmodel()
        exits_model = 0.0
        print(START_UNIX_TIME)
        while True:
            if time.time() - 1 <= START_UNIX_TIME:
                continue  # not game start
            now_time = time.perf_counter()
            if now_turn == 0:
                get_game_set(TEAM_ID)
                check = get_panel_score()
                filename = ["A-1", "A-2", "A-3", "A-4", "B-1", "B-2", "B-3", "C-1", "C-2", "D-1", "D-2", "E-1", "E-2", "F-1", "F-2"]
                dirname = str(HEIGHT) + "-" + str(WIDTH)
                for name in filename:
                    with open("/home/jellyfish/procon30/simulator/build/public-field/" + name + ".json") as file:
                        json_data = json.load(file)
                        if HEIGHT != json_data["height"] or WIDTH != json_data["width"]:
                            break
                        json_data["points"] = np.array(json_data["points"], dtype=float)
                        if np.allclose(check, json_data["points"]):
                            dirname = name
                            break
                print(dirname)
                if os.path.exists(basedir + dirname + "/model.h5"):
                    main_model = load_model(basedir + dirname + "/model.h5")
                else:
                    main_model = create_Qmodel()
                    exits_model = 0.3
            panel_score = get_panel_score()
            game_status = get_game_status(TEAM_ID)
            my_action = []
            my_type = []
            my_coordinate = []
            for i in range(NUMBER_OF_AGENTS):
                my_input = get_my_coordinate(TEAM_ID, AGENTS[i])
                my_enemy_input = get_enemy_coordinate(TEAM_ID)
                next_action, action_point, action_coordinate = get_action(main_model, panel_score, game_status, my_input, my_enemy_input, now_turn, exits_model, TEAM_ID, AGENTS[i], my_coordinate)
                my_coordinate.append(action_coordinate)
                if next_action == 16:
                    my_action.append([0, 0])
                    my_type.append("stay")
                else:
                    my_action.append(SET_LIST[next_action % 8])
                    my_type.append(ACTION[math.floor(next_action / 8)])
            post_agent_action(AGENTS, my_action, my_type)
            output = False
            while True:
                end_time = time.perf_counter()
                if (end_time - now_time) * 1000 >= interval_millisecond + turn_millisecond:
                    break
                elif (end_time - now_time) * 1000 >= turn_millisecond + 50 and not output:
                    print("turn: " + str(now_turn + 1) + ", my score: %d, enemy score %d" % get_reward(TEAM_ID))
                    output = True
            now_turn += 1
            if now_turn == MAX_TURN:
                break
