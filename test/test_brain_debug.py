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

creatures = extract_creatures_with_brain_nodes("logs/turn_logs.jsonl")
print(f"Found {len(creatures)} creatures with brain_nodes")
print(creatures)
#2419, 1075,1053