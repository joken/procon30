import time
import json
import urllib.request
import random
import sys

url = sys.argv[1]
n_agent = int(sys.argv[2])

headers = {
    'Content-Type': 'application/json',
}

while True:
    data = {"actions":[]}

    for i in range(n_agent):
        action = {}

        action["agentID"] = i
        action["dx"] = random.randint(-1, 1)
        action["dy"] = random.randint(-1, 1)
        action["type"] = "move"

        data["actions"].append(action)

    request = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
    with urllib.request.urlopen(request) as responce:
        print(responce.read().decode("utf-8"))

    time.sleep(1)
