import json
import os
import pandas as pd


def load_json(filename):
    with open(os.path.join("data", filename), encoding="utf-8") as f:
        return json.load(f)

def load_combinations():
    return load_json("combinations.json")

def load_elements():
    return load_json("elements.json")

def load_roman():
    return load_json("roman.json")

def load_scoreboard():
    return pd.read_csv(os.path.join("data", 'scoreboard.csv'))

def load_to_scoreboard(data):
    data.to_csv(os.path.join("data", 'scoreboard.csv'), index=False)
