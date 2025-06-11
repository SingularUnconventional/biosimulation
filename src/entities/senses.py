from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.organism import Creature
from src.utils.constants import *
from dataclasses import dataclass
import heapq
import numpy as np

def sense_environment(
    creature: 'Creature',
    count: int,
    range_level: int,
    attention_creature: 'Creature',
    active_senses: set[str],
    slot_map: dict[int, tuple[str, int | None]]
) -> dict:

    cpos = creature.position
    results = {}
    visual_creatures = [creature] #집중 개체의 인덱스를 확인하기 위해 생성한 특수 인자.
    
    # === 1. food 감지 ===
    if {'food_pos_x', 'food_pos_y'} & active_senses:
        min_dx, min_dy = 0, 0
        min_dist_sq = float('inf')
        for corpse in creature.grid.corpses:
            dx = corpse.position.x - cpos.x
            dy = corpse.position.y - cpos.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist_sq:
                min_dx, min_dy = dx, dy
                min_dist_sq = dist_sq
        results['food_pos_x'] = [min_dx/GRID_WIDTH_SCALE]
        results['food_pos_y'] = [min_dy/GRID_HIGHT_SCALE]

    # === 2. 시각 감지 ===
    if {'detected_pos_x', 'detected_pos_y', 'detected_size'} & active_senses:
        if range_level == 0:
            search_set = creature.grid.creatures
        else:
            search_set = creature.grid.vision_refs[range_level - 1]

        candidates = (
            (
                (dx := other.position.x - cpos.x) ** 2 +
                (dy := other.position.y - cpos.y) ** 2,
                dx/GRID_WIDTH_SCALE, 
                dy/GRID_HIGHT_SCALE,
                other.traits.size/creature.traits.size,
                other
            )
            for other in search_set
            if other is not creature
        )

        top_n = heapq.nsmallest(count, candidates)

        if top_n:
            _, dxs, dys, sizes, creatures = zip(*top_n)
            results['detected_pos_x'] = list(dxs)
            results['detected_pos_y'] = list(dys)
            results['detected_size']  = list(sizes)
            visual_creatures += list(creatures)
        else:
            results['detected_pos_x'] = []
            results['detected_pos_y'] = []
            results['detected_size'] = []

    # === 3. 청각 감지 ===
    if 'audio_heard' in active_senses:
        results['audio_heard'] = creature.grid.crying_sound[1]  # dict[int] or list[float]

    # === 4. 주의 감지 ===
    if {'focus_pos_x', 'focus_pos_y', 'focus_size', 'focus_similarity', 'focus_diet_type', 'focus_health','focus_color_saturation', 'focus_color_hue', 'focus_hunger'} & active_senses and attention_creature is not None:
        results.update({
        'focus_pos_x': [(attention_creature.position.x - cpos.x) / creature.traits.size],
        'focus_pos_y': [(attention_creature.position.y - cpos.y) / creature.traits.size],
        'focus_size': [attention_creature.traits.size / creature.traits.size],
        'focus_similarity': [creature.get_species_similarity(attention_creature)],
        'focus_diet_type': [attention_creature.traits.food_intake],
        'focus_health': [attention_creature.health / attention_creature.traits.health],
        'focus_color_saturation': [attention_creature.traits.species_color_rgb[1]],
        'focus_color_hue': [attention_creature.traits.species_color_rgb[0]],
        'focus_hunger': [attention_creature.energy / attention_creature.traits.energy_reserve],
    })

    #print("=== DEBUG: audio_heard in results ===")
    #print(results.get('audio_heard'))
    #print(type(results.get('audio_heard')))

    # === 5. slot_map에 따라 필요한 값만 추출 ===
    output = {}
    for slot, (key, idx) in slot_map.items():
        value = results.get(key)
        if value is None:
            continue
        if idx is None:
            output[slot] = value
        elif isinstance(value, dict):
            output[slot] = value.get(idx, 0)
        elif isinstance(value, (list, tuple)) and 0 <= idx < len(value):
            output[slot] = value[idx]
        else:
            output[slot] = 0

    return output, visual_creatures