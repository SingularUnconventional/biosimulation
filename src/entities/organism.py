from src.core.engine        import World, Grid
from src.entities.genome    import Genome
from src.utils.constants    import *
from src.utils.datatypes    import Color, Vector2, Genes, Traits
from src.utils.math_utils   import find_closest_point_arg, find_closest_point, get_grid_coords

import numpy as np


class Creature:
    _id_counter = 0  # 클래스 변수: 모든 Creature 인스턴스가 공유

    def __init__(self, 
                 position       : Vector2, 
                 genome_bytes   : bytes, 
                 world          : World,
                 grid           : Grid,
                 start_energy   : float,
                 ):
        self.genome = Genome(genome_bytes)
        self.traits = Traits(self.genome.traits)

        self.world          : World     = world
        self.grid           : Grid      = grid
        self.position       : Vector2   = position
        self.health         : float     = self.traits.health
        self.energy         : float     = start_energy
        self.alive          : bool      = True
        
        self.id = Creature._id_counter  # 고유 ID 부여
        Creature._id_counter += 1       # 다음 ID 준비

        self._locate = Vector2(np.random.uniform(-1, 1), np.random.uniform(-1, 1))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Creature) and self.id == other.id
    
    def update(self) -> list["Creature"] | str | None:
        
        for i, organic in enumerate(self.grid.organics.current_amounts):
            if self.traits.food_intake_rates[i] and organic-self.traits.food_intake_rates[i] > 0:
                self.energy                             += self.traits.food_intake_rates[i]
                self.grid.organics.current_amounts[i]   -= self.traits.food_intake_rates[i]
        self.energy -= self.traits.BMR

        # 죽음
        if self.energy <= 0:
            return "die"

        # 이동 및 번식
        offspring = self.move()
        if offspring:
            return offspring  # 자식 리스트 반환
        
        return None

    def move(self):
        if self.energy > self.traits.initial_offspring_energy*self.traits.offspring_count*2:
            return self.breed()
        
        new_position = self._locate*self.traits.speed + self.position
    
        if (new_position.x < 0 or 
            new_position.y < 0 or 
            new_position.x >= WORLD_WIDTH_SCALE*GRID_WIDTH_SCALE or 
            new_position.y >= WORLD_HIGHT_SCALE*GRID_HIGHT_SCALE): #임시. 차후 테두리는 생존 불가능 구역으로 설정하여 문제 해결.
            new_position = Vector2(WORLD_WIDTH_SCALE*GRID_WIDTH_SCALE/2, WORLD_HIGHT_SCALE*GRID_HIGHT_SCALE/2)
            
        self.position = new_position
        new_grid = get_grid_coords(self.position)
        
        if self.grid.pos != new_grid:
            return "move"

        
        return None

    def eat(self):
        if self.energy < self.traits.energy_reserve:
            foodLength, foodNum = find_closest_point(
                points=np.array([[food.position.x, food.position.y] for food in self.world.foods]),
                target=np.array([self.position.x, self.position.y])
            )

            food = self.world.foods[foodNum]

            if foodLength < self.traits.speed:
                self.energy += food.energy
                del self.world.foods[foodNum]
            
    def breed(self):
        self.energy -= self.traits.initial_offspring_energy*self.traits.offspring_count
        return [Creature(
                self.position+Vector2(-np.random.random(), -np.random.random()), 
                self.genome.crossover(self.genome.genome_bytes, self.traits.mutation_intensity), 
                self.world, 
                self.grid,
                self.traits.initial_offspring_energy) for _ in range(self.traits.offspring_count)]
        
#임시
class Food_:
    def __init__(self):
        self.position    : Vector2
        self.energy      : int = FOOD_START_ENERGY

        self.regenerate()

    def regenerate(self):
        self.position = Vector2(
                        np.random.uniform(WORLD_WIDTH_SCALE), 
                        np.random.uniform(WORLD_HIGHT_SCALE))