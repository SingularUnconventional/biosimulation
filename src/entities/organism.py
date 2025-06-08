# creature.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.engine import World, Grid

from src.entities.brain     import brain_calculation
from src.entities.genome    import Genome
from src.entities.senses    import sense_environment
from src.entities.actions   import actions_environment
from src.utils.constants    import *
from src.utils.datatypes    import Color, Vector2, Genes, Traits
from src.utils.trait_computer import compute_biological_traits
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
        self.traits = compute_biological_traits(self.genome.traits)

        self.world          : 'World'   = world
        self.grid           : 'Grid'    = grid
        self.position       : Vector2   = position
        self.health         : float     = self.traits.health
        self.energy         : float     = self.traits.initial_offspring_energy
        self.life_start_time: int       = world.time
        self.brain_nodes    : np.ndarray= np.zeros((self.traits.brain_max_nodeInx+1, 3))

        self.move_speed = 1
        self.move_dir_x = np.random.uniform(-1, 1)
        self.move_dir_y = np.random.uniform(-1, 1)
        self.attack_intent = 1
        self.reproduce_intent = 1
        self.eat_intent = 1
        self.cry_volume = [0 for _ in range(10)]
        self.attention_creature = self
        

        self.id = Creature._id_counter  # 고유 ID 부여
        Creature._id_counter += 1       # 다음 ID 준비

        self.move()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Creature) and self.id == other.id
    
    def find_creatures_within(self, max_distance: float) -> list['Creature']:
        """같은 grid 내에서 자신을 제외하고 특정 거리 이하의 모든 개체를 반환"""
        others = [c for c in self.grid.creatures if c is not self]
        if not others:
            return []

        self_pos = np.array([self.position.x, self.position.y])
        positions = np.array([[c.position.x, c.position.y] for c in others])

        deltas = positions - self_pos
        dists_sq = np.einsum("ij,ij->i", deltas, deltas)
        max_dist_sq = max_distance ** 2

        # 거리 제한 이하인 인덱스 필터링
        valid_indices = np.where(dists_sq <= max_dist_sq)[0]

        return [others[i] for i in valid_indices]
    
    def update(self) -> list["Creature"] | str | None:
        if self.brain_nodes != []:
            InputNodes = sense_environment(
                creature= self,
                count= self.traits.visible_entities,
                range_level= self.traits.auditory_range,
                attention_creature= self.attention_creature,
                active_senses= self.traits.brain_input_key_set,
                slot_map= self.traits.brain_input_synapses)
            
            for k, v in InputNodes.items():
                self.brain_nodes[k][0] = v

            self.brain_nodes = brain_calculation(self.brain_nodes, self.traits.brain_compute_cycles)

            actions_environment(self, self.brain_nodes, self.traits.brain_output_synapses)
        
        self.energy -= self.traits.BMR
        if self.eat_intent:
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

            if self.attack_intent:
                for creature in self.find_creatures_within(self.traits.size/2):
                    creature.health -= self.traits.attack_power
                    self.health -= creature.traits.retaliation_damage
                    creature.energy -= self.traits.attack_cost

        # 죽음
        if (self.energy < self.traits.energy_reserve*0.3 or 
            self.life_start_time+self.traits.lifespan < self.world.time or
            self.health < 0):
            return "die"
        
        if self.energy > self.traits.initial_offspring_energy*self.traits.offspring_count*2 and self.reproduce_intent:
            return self.breed()

        # 이동
        if self.traits.speed == 0 or self.traits.speed == 0: return None

        return self.move()
        

    def move(self):
        new_position = Vector2(self.move_dir_x, self.move_dir_y)*self.traits.speed*self.move_speed + self.position
    
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
                self.position+Vector2(
                np.cos(theta := np.random.uniform(0, 2 * np.pi)) * self.traits.size,
                np.sin(theta) * self.traits.size
            ), 
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