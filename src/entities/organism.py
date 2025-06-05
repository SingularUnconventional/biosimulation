# creature.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.engine import World, Grid

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
                 world          : 'World',
                 grid           : 'Grid',
                 start_energy   : float,
                 ):
        self.genome = Genome(genome_bytes)
        self.traits = Traits(self.genome.traits)

        self.world          : 'World'   = world
        self.grid           : 'Grid'    = grid
        self.position       : Vector2   = position
        self.health         : float     = self.traits.health
        self.energy         : float     = self.traits.initial_offspring_energy
        self.life_start_time: int       = world.time
        
        self.id = Creature._id_counter  # 고유 ID 부여
        Creature._id_counter += 1       # 다음 ID 준비

        self._locate = Vector2(np.random.uniform(-1, 1), np.random.uniform(-1, 1))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Creature) and self.id == other.id
    
    def update(self) -> list["Creature"] | str | None:
        
        self.energy -= self.traits.BMR
        if self.traits.food_intake == 0: #태양에너지.
            if (self.grid.organics[self.traits.food_intake] > self.traits.intake_rates 
            and self.energy < self.traits.energy_reserve):
                self.energy     += self.traits.actual_intake * self.world.solar_conversion_bonus
                self.grid.organics[self.traits.food_intake]  -= self.traits.intake_rates * self.world.solar_conversion_bonus
        elif self.traits.food_intake == 4: #사체 섭취
            ...
        else:
            if (self.grid.organics[self.traits.food_intake] > self.traits.intake_rates 
            and self.energy < self.traits.energy_reserve):
                self.energy     += self.traits.actual_intake
                self.grid.organics[self.traits.food_intake] -= self.traits.intake_rates

        

        # 죽음
        if self.energy <= self.traits.energy_reserve*0.3 or self.life_start_time+self.traits.lifespan < self.world.time:
            return "die"
        
        if self.energy > self.traits.initial_offspring_energy*self.traits.offspring_count*2:
            return self.breed()

        # 이동 및 번식
        return self.move()

    def move(self):
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
        
#음식 -> 시체 개편.
class Corpse:
    def __init__(self, grid, position, energy):
        self.grid       : 'Grid'    = grid
        self.position    : Vector2  = position
        self.energy      : float    = energy

    def decay(self):
        for i in range(NUM_ORGANIC):
            self.grid.organics[i] += DECAY_RETURN_ENERGY[i]
            self.energy -= DECAY_RETURN_ENERGY[i]

        if self.energy < 0:
            return "die"
        else:
            return None