from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.organism import Creature


def actions_environment(
    creature: 'Creature',
    node: list[list[float]],
    slot_map: dict[int, tuple[str, int | None]]
) -> None:
    
    """node와 slot_map을 기반으로 creature에 행동 적용"""
    for inx, row in enumerate(node):
        value = row[1]

        # 해당 slot이 action 출력용인지 확인
        mapping = slot_map.get(inx)
        if not mapping:
            continue

        action_key, index = mapping

        # 해당 action을 creature에 적용
        if action_key == 'move_speed_out':
            creature.move_speed = 1-value
        elif action_key == 'move_x_out':
            creature.move_dir_x = (value-0.5)*2
        elif action_key == 'move_y_out':
            creature.move_dir_y = (value-0.5)*2
        elif action_key == 'attack_out':
            creature.attack_intent = value < 0.5
        elif action_key == 'reproduce_out':
            creature.reproduce_intent = value < 0.5
        elif action_key == 'eat_out':
            creature.eat_intent = value < 0.5
        elif action_key == 'cry_out':
            creature.cry_volume[int(index)] = value < 0.5
        elif action_key == 'attention_selected':
            # TODO: attention_creature 개선
            creature.attention_creature = creature