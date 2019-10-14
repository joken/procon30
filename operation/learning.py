import subprocess
import common
import numpy as np

if __name__ == "__main__":
    height = 10
    width = 10
    port = 8081
    agent = 3
    filepath = common.random_field(height, width, agent, port)
    get = subprocess.run(["python", "/home/jellyfish/procon30/operation/solver.py",
                          str(60), filepath, str(height) + "-" + str(width) + "temp", str(port)])
