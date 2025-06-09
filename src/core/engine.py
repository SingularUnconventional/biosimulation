from src.data.logger        import WorldLog
from src.entities.organism  import Corpse, Creature
from src.entities.environment import OrganicMatterSource
from src.utils.datatypes    import Vector2, Traits, Genes
from src.utils.constants    import *
from src.utils.math_utils   import get_grid_coords
from src.utils.noise_fields import generate_noise_field

import numpy as np

class World:
    
    def __init__(self):
        self.time = 0

        self.solar_conversion_bonus = 5000

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
            creature = Creature(pos, np.random.randint(0, 256, 1500, dtype=np.uint8).tobytes(), self, self.world[gridPos.y][gridPos.x], 0)
            self.world[gridPos.y][gridPos.x].creatures.add(creature)
            self.logs.register_creature({creature})

    def build_vision_refs(self, max_radius: int):
        """모든 Grid에 대해 시야 반경별 creatures 참조 리스트 생성"""
        for y in range(WORLD_HIGHT_SCALE):
            for x in range(WORLD_WIDTH_SCALE):
                grid = self.world[y][x]
                grid.vision_refs = []  # radius: List[Set[Creature]]

                for r in range(1, max_radius + 1):
                    refs = set()
                    for dy in range(-r, r + 1):
                        ny = y + dy
                        if not (0 <= ny < WORLD_HIGHT_SCALE):
                            continue
                        for dx in range(-r, r + 1):
                            nx = x + dx
                            if not (0 <= nx < WORLD_WIDTH_SCALE):
                                continue
                            neighbor = self.world[ny][nx]
                            refs.update(neighbor.creatures)
                    grid.vision_refs.append(refs)

    def Trun(self):
        for yGrid in self.world:
            for grid in yGrid:
                grid.process_creatures(self)
                grid.turn()
                #grid.organics.regenerate()
        self.logs.log_turn()
        #print(self.time)
        self.time += 1

class Grid:
    def __init__(self, x: int, y: int, organic_affinity: list[float]):
        self.pos = Vector2(x, y)
        self.creatures = set()
        self.corpses = set()
        self.vision_refs = []  # 시야 반경별 참조 리스트 초기화

        self.organics = [((organic_affinity[i] + 1) * 0.5 * START_ORGANIC_RATES[i]) for i in range(NUM_ORGANIC)]
        # self.organics = OrganicMatterSource([
        #     ((organic_affinity[i] + 1) * 0.5 * ORGANIC_GEN_RATE[i],
        #      (organic_affinity[i] + 1) * 0.5 * ORGANIC_MAX_AMOUNT[i])
        #     for i in range(NUM_ORGANIC)
        # ])

        self.crying_sound = [[0 for _ in range(1000)] for _ in range(2)]

    def turn(self):
        self.crying_sound[1] = self.crying_sound[0] #말하기 채널 값을 듣기 채널로 이동.
        self.crying_sound[0] = [0]*1000             #말하기 채널 초기화.
        
    def process_creatures(self, world: World):
        creature_spawn_queue = set()
        creature_remove_queue = set()
        corpse_remove_queue = set()

        for creature in list(self.creatures):  # 안전한 복사 반복
            result = creature.update()

            # 죽음
            if result == "die":
                self.corpses.add(Corpse(self, creature.position, creature.energy))
                creature_remove_queue.add(creature)

            # 번식
            elif isinstance(result, list):  # 여러 자식 Creature 반환
                creature_spawn_queue.update(result)

            # 이동
            elif result == "move":
                new_grid = get_grid_coords(creature.position)
                self.creatures.discard(creature)
                world.world[new_grid.y][new_grid.x].creatures.add(creature)
                creature.grid = world.world[new_grid.y][new_grid.x]  # 업데이트 필수

        for corpse in list(self.corpses):
            result = corpse.decay()

            if result and result == "die":
                corpse_remove_queue.add(corpse)

        for creature in creature_remove_queue:
            self.creatures.discard(creature)

        
        for corpse in corpse_remove_queue:
            self.corpses.discard(corpse)

        for offspring in creature_spawn_queue:
            offspring.move() #TODO 공간 벗어남 문제 임시 해결. x추가 후 삭제.
            c = get_grid_coords(offspring.position)
            world.world[c.y][c.x].creatures.add(offspring)
            offspring.grid = world.world[c.y][c.x]

        world.logs.register_creature(creature_spawn_queue)