import subprocess
from multiprocessing import Process
import getpass
import numpy as np
import math
import json


class Gamebord_exec:
    pid = 0

    # constructor
    def __init__(self, interval_millisec, turn_millisec, max_turn, between, filepath, port, no_time):
        self.__interval_millisec = interval_millisec
        self.__turn_millisec = turn_millisec
        self.__max_turn = max_turn
        self.__between = between
        self.__filepath = filepath
        self.__notime = no_time
        self.__port = port

    def server_start(self, get):
        # self is Process member variables, Don't use.
        username = getpass.getuser()
        get.__popen = subprocess.Popen(["/home/" + str(username) + "/procon30/simulator/build/procon30-simulator", str(get.__interval_millisec), str(get.__turn_millisec),
                                        str(get.__max_turn), str(get.__between), str(get.__filepath), str(get.__port), get.__notime], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start(self):
        self.__process = Process(target=self.server_start(self))
        self.__process.start()
        self.__process.join()

    def end(self):
        self.__popen.kill()
        self.__process.kill()


def random_field(height, width, number_of_agents, port):
    filepath = "./field/" + str(port) + ".json"
    json_data = {"width": width, "height": height}
    pattan = np.random.randint(0, 3)
    field_points = []
    # print(field_points)
    field_tiles = []
    for y in range(height):
        x_field = []
        x_tiles = []
        for x in range(width):
            x_field.append(np.random.randint(-16, 17))
            x_tiles.append(0)
            if x_field[x] < 0 and np.random.randint(0, 3) < 1:
                x_field[x] = np.random.randint(0, 17)
        field_points.append(x_field)
        field_tiles.append(x_tiles)
    if pattan == 0:
        # Line symmetry (width)
        for x in range(math.floor(width / 2)):
            for y in range(height):
                field_points[y][width - x - 1] = field_points[y][x]
    elif pattan == 1:
        # Line symmetry (height)
        for y in range(math.floor(height / 2)):
            for x in range(width):
                field_points[height - y - 1][x] = field_points[y][x]
    else:
        # Point symmetry
        for y in range(math.floor(height / 2)):
            for x in range(math.floor(width / 2)):
                field_points[height - y - 1][x] = field_points[y][x]
                field_points[y][width - x - 1] = field_points[y][x]
                field_points[height - y - 1][width -
                                             x - 1] = field_points[y][x]
    my_agents = []
    enemy_agents = []
    for i in range(number_of_agents):
        agent_x = 0
        agent_y = 0
        if pattan == 0:
            agent_x = np.random.randint(0, math.ceil(width / 2))
            agent_y = np.random.randint(0, height)
            team_id = np.random.randint(1, 3)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
            agent_x = width - agent_x - 1
            team_id = (2 if team_id == 1 else 1)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
        elif pattan == 1:
            agent_x = np.random.randint(0, width)
            agent_y = np.random.randint(0, math.ceil(height / 2))
            team_id = np.random.randint(1, 3)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
            agent_y = height - agent_y - 1
            team_id = (2 if team_id == 1 else 1)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
        else:
            agent_x = np.random.randint(0, width)
            agent_y = np.random.randint(0, math.ceil(height / 2))
            team_id = np.random.randint(1, 3)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
            agent_x = width - agent_x - 1
            agent_y = height - agent_y - 1
            team_id = (2 if team_id == 1 else 1)
            field_tiles[agent_y][agent_x] = team_id
            if team_id == 1:
                my_agents.append(
                    {"agentID": i + 1, "x": agent_x + 1, "y": agent_y + 1})
            else:
                enemy_agents.append(
                    {"agentID": number_of_agents + i + 1, "x": agent_x + 1, "y": agent_y + 1})
    json_data["points"] = field_points
    json_data["startedAtUnixTime"] = 0
    json_data["turn"] = 0
    json_data["tiled"] = field_tiles
    team = []
    my_team = {"teamID": 1}
    my_team["agents"] = my_agents
    my_team["tilePoint"] = 0
    my_team["areaPoint"] = 0
    team.append(my_team)
    enemy_team = {"teamID": 2}
    enemy_team["agents"] = enemy_agents
    enemy_team["tilePoint"] = 0
    enemy_team["areaPoint"] = 0
    team.append(enemy_team)
    json_data["teams"] = team
    actions = []
    json_data["actions"] = actions
    with open(filepath, 'w') as f:
        json.dump(json_data, f, indent=2)
        return filepath
