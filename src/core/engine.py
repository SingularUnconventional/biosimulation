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

        self.solar_conversion_bonus = 50000

        # === 원본 노이즈 생성 ===
        terrain_noise = generate_noise_field(
            shape=(WORLD_WIDTH_SCALE, WORLD_HIGHT_SCALE),
            scale=20,
            seeds=np.random.randint(100)
        )

        organics_noise = generate_noise_field(
            shape=(WORLD_WIDTH_SCALE, WORLD_HIGHT_SCALE),
            scale=WORLD_WIDTH_SCALE / 1,
            seeds=[np.random.randint(100) for _ in range(NUM_ORGANIC)]
        )

        # === 초기화 및 기본 복사 ===
        terrain_with_border = np.full((WORLD_WIDTH_SCALE + 4, WORLD_HIGHT_SCALE + 4, 1), fill_value=2.0, dtype=float)
        organics_with_border = np.zeros((WORLD_WIDTH_SCALE + 4, WORLD_HIGHT_SCALE + 4, 4), dtype=float)

        # === 내부에 원본 삽입 ===
        terrain_with_border[2:-2, 2:-2] = terrain_noise
        organics_with_border[2:-2, 2:-2] = organics_noise

        # === 외곽 테두리 값 설정 ===
        terrain_with_border[0:1, :] = 6000  # 상단 2줄
        terrain_with_border[-1:, :] = 6000  # 하단 2줄
        terrain_with_border[:, 0:1] = 6000  # 좌측 2줄
        terrain_with_border[:, -1:] = 6000  # 우측 2줄

        # === 최종 할당 ===
        terrain_noise = terrain_with_border
        organics_noise = organics_with_border
        
        terrain_noise = self.save_altitude_from_noise(terrain_noise)

        self.world = [[
            Grid(xGrid, yGrid, terrain_noise[yGrid, xGrid], organics_noise[yGrid, xGrid])
            for xGrid in range(WORLD_WIDTH_SCALE+4)]
            for yGrid in range(WORLD_HIGHT_SCALE+4)
        ]
        
        self.logs = WorldLog(self.world)

        self.build_vision_refs(max_radius=4)  # 시야 반경 1~4까지 지원

        for _ in range(CREATURES_SIZE):
            pos = Vector2(np.random.uniform(GRID_WIDTH_SCALE*2, GRID_WIDTH_SCALE*(WORLD_WIDTH_SCALE+2)), 
                          np.random.uniform(GRID_HIGHT_SCALE*2, GRID_HIGHT_SCALE*(WORLD_HIGHT_SCALE+2)))
            gridPos = get_grid_coords(pos)
            creature = Creature(pos, np.random.randint(0, 256, 3000, dtype=np.uint8).tobytes(), self, self.world[gridPos.y][gridPos.x], 0)
            self.world[gridPos.y][gridPos.x].creatures.add(creature)
            self.logs.register_creature({creature})

    
    def save_altitude_from_noise(self, terrain_noise: np.ndarray, save_path: str = "logs/terrain_altitude.npy"):
        """
        [-1.0, 1.0] 범위의 노이즈를 0~20 사이의 정수 고도값으로 변환하여 저장
        """
        altitude = ((terrain_noise + 1) * 10).astype(np.uint16)  # 정수 변환
        np.save(save_path, altitude)
        return altitude

    def build_vision_refs(self, max_radius: int):
        """모든 Grid에 대해 시야 반경별 creatures 참조 리스트 생성"""
        for y in range(2, WORLD_HIGHT_SCALE+2):
            for x in range(2, WORLD_WIDTH_SCALE+2):
                grid = self.world[y][x]
                grid.vision_refs = []  # radius: List[Set[Creature]]

                for r in range(1, max_radius + 1):
                    refs = set()
                    for dy in range(-r, r + 1):
                        ny = y + dy
                        if not (2 <= ny < WORLD_HIGHT_SCALE+2):
                            continue
                        for dx in range(-r, r + 1):
                            nx = x + dx
                            if not (2 <= nx < WORLD_WIDTH_SCALE+2):
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
    def __init__(self, x: int, y: int, terrain_noise: int, organic_affinity: list[float]):
        self.pos = Vector2(x, y)
        self.creatures = set()
        self.corpses = set()
        self.vision_refs = [[] for _ in range(4)]  # 시야 반경별 참조 리스트 초기화

        self.terrain = terrain_noise

        self.organics = [((organic_affinity[i] + 1) * 0.5 * START_ORGANIC_RATES[i]) for i in range(NUM_ORGANIC)]
        # self.organics = OrganicMatterSource([
        #     ((organic_affinity[i] + 1) * 0.5 * ORGANIC_GEN_RATE[i],
        #      (organic_affinity[i] + 1) * 0.5 * ORGANIC_MAX_AMOUNT[i])
        #     for i in range(NUM_ORGANIC)
        # ])

        self.crying_sound = [[0 for _ in range(1000)] for _ in range(2)]
        self.crying_sound_set = set()

    def turn(self):
        self.crying_sound[1] = self.crying_sound[0] #말하기 채널 값을 듣기 채널로 이동.
        self.crying_sound[0] = [0]*1000             #말하기 채널 초기화.
        
    def process_creatures(self, world: World):
        self.crying_sound_set = set()
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
            c = get_grid_coords(offspring.position)
            world.world[c.y][c.x].creatures.add(offspring)
            offspring.grid = world.world[c.y][c.x]

        world.logs.register_creature(creature_spawn_queue)