import json
import numpy as np
def extract_creatures_with_brain_nodes(log_file_path: str):
    """
    brain_nodes 정보가 있는 creature만 추출
    :param log_file_path: 로그 jsonl 파일 경로
    :return: List[Dict] (id, x, y, health, energy, brain_nodes)
    """
    result = []

    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            turn_data = json.loads(line)
            grids = turn_data[1]

            for row in grids:
                for grid in row:
                    creatures = grid[1]  # [organics, creatures, corpses]
                    for c in creatures:
                        if c[5] != [] and isinstance(c[5], list):
                            result.append({
                                "id": c[0],
                                "x": c[1],
                                "y": c[2],
                                "health": c[3],
                                "energy": c[4],
                                "brain_nodes": c[5]
                            })

    return result

# creatures = extract_creatures_with_brain_nodes("logs/turn_logs.jsonl")
# print(f"Found {len(creatures)} creatures with brain_nodes")
# print([(creature['id'], creature['x'], creature['y']) for creature in creatures])
import json
import time
from pathlib import Path

LOG_PATH = "logs/turn_logs.jsonl"

def monitor_creature_movement(log_path):
    id_positions = {}
    last_file_pos = 0

    while True:
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                f.seek(last_file_pos)
                new_lines = f.readlines()
                last_file_pos = f.tell()
        except FileNotFoundError:
            time.sleep(1)
            continue

        for line in new_lines:
            try:
                turn_data = json.loads(line)
            except json.JSONDecodeError as e:
                print("JSON Decode Error:", e)
                continue

            grids = turn_data[1]
            for row in grids:
                for grid in row:
                    creatures = grid[1]
                    for c in creatures:
                        cid, x, y = c[0], c[1], c[2]
                        prev_pos = id_positions.get(cid)
                        if prev_pos and (prev_pos[0] != x or prev_pos[1] != y):
                            print(f"Moved: {cid} from {prev_pos} to {(x, y)}\a") 
                        id_positions[cid] = (x, y)

        time.sleep(0.5)  # 감시 주기

if __name__ == "__main__":
    print(f"\a") 
    monitor_creature_movement(LOG_PATH)

