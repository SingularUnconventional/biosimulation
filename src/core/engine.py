from src.data.logger        import WorldLog
from src.entities.environment import OrganicMatterSource
from src.utils.datatypes    import Vector2, Traits, Genes
from src.utils.constants    import *
from src.utils.math_utils   import get_grid_coords
from src.utils.noise_fields import generate_noise_field

import numpy as np

class World:
    
    def __init__(self):
        from src.entities.organism import Creature

        organics_noise = generate_noise_field(
            shape=(WORLD_WIDTH_SCALE, WORLD_HIGHT_SCALE),
            scale=WORLD_WIDTH_SCALE / 1,
            seeds=[np.random.randint(100) for _ in range(NUM_ORGANIC)]
        )

        self.world = [[
            Grid(xGrid, yGrid, organics_noise[yGrid, xGrid])
            for xGrid in range(WORLD_WIDTH_SCALE)]
            for yGrid in range(WORLD_HIGHT_SCALE)
        ]
        
        self.logs = WorldLog(self.world)

        self.build_vision_refs(max_radius=3)  # 시야 반경 1~3까지 지원

        for _ in range(CREATURES_SIZE):
            pos = Vector2(np.random.uniform(GRID_WIDTH_SCALE*WORLD_WIDTH_SCALE), np.random.uniform(GRID_HIGHT_SCALE*WORLD_HIGHT_SCALE))
            gridPos = get_grid_coords(pos)
            creature = Creature(pos, np.random.randint(0, 256, 150, dtype=np.uint8).tobytes(), self, self.world[gridPos.y][gridPos.x], 0)
            self.world[gridPos.y][gridPos.x].creatures.add(creature)

    def build_vision_refs(self, max_radius: int):
        """모든 Grid에 대해 시야 반경별 creatures 참조 리스트 생성"""
        for y in range(WORLD_HIGHT_SCALE):
            for x in range(WORLD_WIDTH_SCALE):
                grid = self.world[y][x]
                grid.vision_refs = []  # radius: List[List[Creature]]
                for r in range(1, max_radius + 1):
                    refs = []
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < WORLD_WIDTH_SCALE and 0 <= ny < WORLD_HIGHT_SCALE:
                                neighbor = self.world[ny][nx]
                                refs.append(neighbor.creatures)  # 참조만 저장
                    grid.vision_refs.append(refs)

    def Trun(self):
        for yGrid in self.world:
            for grid in yGrid:
                grid.process_creatures(self)
                grid.organics.regenerate()
        self.logs.log_turn()

class Grid:
    def __init__(self, x: int, y: int, organic_affinity: list[float]):
        self.pos = Vector2(x, y)
        self.creatures = set()
        self.vision_refs = []  # 시야 반경별 참조 리스트 초기화

        self.organics = OrganicMatterSource([
            ((organic_affinity[i] + 1) * 0.5 * ORGANIC_GEN_RATE[i],
             (organic_affinity[i] + 1) * 0.5 * ORGANIC_MAX_AMOUNT[i])
            for i in range(NUM_ORGANIC)
        ])

    def process_creatures(self, world: World):
        spawn_queue = set()
        remove_queue = set()

        for creature in list(self.creatures):  # 안전한 복사 반복
            result = creature.update()

            # 죽음
            if result == "die":
                remove_queue.add(creature)

            # 번식
            elif isinstance(result, list):  # 여러 자식 Creature 반환
                spawn_queue.update(result)

            # 이동
            elif result == "move":
                new_grid = get_grid_coords(creature.position)
                self.creatures.discard(creature)
                world.world[new_grid.y][new_grid.x].creatures.add(creature)
                creature.grid = world.world[new_grid.y][new_grid.x]  # 업데이트 필수

        for creature in remove_queue:
            self.creatures.discard(creature)

        for offspring in spawn_queue:
            c = get_grid_coords(offspring.position)
            world.world[c.y][c.x].creatures.add(offspring)

        world.logs.register_creature(spawn_queue)