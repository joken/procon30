import subprocess
import common
import numpy as np

if __name__ == "__main__":
    for height in range(10, 21):
        for width in range(10, 21):
            print(str(height) + "-" + str(width))
            port = 8000 + height * 100 + width
            agent = np.random.randint(2, 9)
            filepath = common.random_field(height, width, agent, port)
            get = subprocess.run(["python", "/home/jellyfish/procon30/operation/solver.py",
                                  str(60), filepath, str(height) + "-" + str(width), str(port)])
