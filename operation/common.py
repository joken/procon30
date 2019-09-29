import subprocess
from multiprocessing import Process
import getpass


class gamebord_exec:
    pid = 0

    # constructor
    def __init__(self, interval_millisec, turn_millisec, max_turn, between, filepath):
        self.__interval_millisec = interval_millisec
        self.__turn_millisec = turn_millisec
        self.__max_turn = max_turn
        self.__between = between
        self.__filepath = filepath

    def server_start(self, get):
        # self is Process member variables, Don't use.
        username = getpass.getuser()
        get.__popen = subprocess.Popen(["/home/" + str(username) + "/procon30/simulator/build/procon30-simulator", str(get.__interval_millisec), str(get.__turn_millisec),
                                        str(get.__max_turn), str(get.__between), str(get.__filepath)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start(self):
        self.__process = Process(target=self.server_start(self))
        self.__process.start()
        self.__process.join()

    def end(self):
        self.__popen.kill()
        self.__process.kill()
