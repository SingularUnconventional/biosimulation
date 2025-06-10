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
from src.utils.math_utils   import find_closest_point, get_grid_coords, find_creatures_within, find_nearest_creature, gene_similarity, find_nearest_corpse

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
        if self.traits.brain_max_nodeInx:
            self.brain_nodes: np.ndarray= np.zeros((self.traits.brain_max_nodeInx+1, 3))
        else:
            self.brain_nodes: np.ndarray= np.array([])

        self.move_speed = 0
        self.move_dir_x = np.random.uniform(-1, 1)
        self.move_dir_y = np.random.uniform(-1, 1)
        self.attack_intent = False
        self.reproduce_intent = True
        self.eat_intent = True
        self.cry_volume = [False]*CRY_VOLUME_SIZE
        self.attention_creature = self

        self._similarity_cache: dict['Creature', float] = {}
        

        self.id = Creature._id_counter  # 고유 ID 부여
        Creature._id_counter += 1       # 다음 ID 준비

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Creature) and self.id == other.id
    
    
    def update(self) -> list["Creature"] | str | None:

        # 뇌
        if self.traits.brain_max_nodeInx:
            for i in range(CRY_VOLUME_SIZE):
                if not self.cry_volume[i]:
                    continue
                
                self.grid.crying_sound[0][self.traits.calls[i]] += 1

            InputNodes, visual_creatures = sense_environment(
                creature= self,
                count= self.traits.visible_entities,
                range_level= self.traits.auditory_range,
                attention_creature= self.attention_creature,
                active_senses= self.traits.brain_input_key_set,
                slot_map= self.traits.brain_input_synapses)


            for _ in range(self.traits.brain_compute_cycles):
                for k, v in InputNodes.items():
                    self.brain_nodes[k][0] = v

                self.brain_nodes = brain_calculation(self.brain_nodes, self.traits.brain_synapses)

            actions_environment(self, self.brain_nodes, self.traits.brain_output_synapses, visual_creatures)
        
        # 에너지
        self.energy -= self.traits.BMR
        if self.eat_intent:
            if self.traits.food_intake == 0: #태양에너지.
                if (self.grid.organics[self.traits.food_intake] > self.traits.intake_rates 
                and self.energy < self.traits.energy_reserve):
                    self.energy     += self.traits.actual_intake * self.world.solar_conversion_bonus
                    self.grid.organics[self.traits.food_intake]  -= self.traits.intake_rates * self.world.solar_conversion_bonus
            elif self.traits.food_intake == 4: #사체 섭취
                corpse = find_nearest_corpse(self, self.grid.corpses, self.traits.size)
                if corpse:
                    corpse.energy -= self.traits.actual_intake
                    self.energy += self.traits.actual_intake
            else:
                if (self.grid.organics[self.traits.food_intake] > self.traits.intake_rates 
                and self.energy < self.traits.energy_reserve):
                    self.energy     += self.traits.actual_intake
                    self.grid.organics[self.traits.food_intake] -= self.traits.intake_rates

        # 근접
        attack_creatures    = find_creatures_within(self, self.grid.creatures, self.traits.attack_range)
        neighbor_creatures  = find_creatures_within(self, attack_creatures, self.traits.size/2)

        if self.attack_intent:
            for creature in attack_creatures:
                creature.health -= self.traits.attack_power
                self.health     -= creature.traits.retaliation_damage
                self.energy     -= self.traits.attack_cost

        if len(neighbor_creatures) >= 2:
            for creature in neighbor_creatures:
                creature.health -= self.traits.crowding_pressure

        #체력

        # 선호 고도와 실제 지형 고도 차이에 따라 감소
        if self.grid.terrain != self.traits.preferred_altitude:
            delta = self.traits.preferred_altitude - self.grid.terrain
            self.health -= ALTITUDE_HEALTH_DECAY*(delta ** 2)

        if self.traits.health > self.health:  
            self.health += self.traits.recovery_rate
            self.energy -= self.traits.recovery_rate

        # 죽음
        if (self.energy < self.traits.energy_reserve*0.3 or 
            self.life_start_time+self.traits.lifespan < self.world.time or
            self.health < 0):
            return "die"
        
        if self.reproduce_intent: # 의지가 있을 때
            if self.traits.reproductive_mode: # 유성생식
                if self.energy > self.traits.all_initial_offspring_energy: # 에너지 충분
                    breed_creatures = find_nearest_creature(self, attack_creatures, self.traits.size)
                    if breed_creatures and self.get_species_similarity(breed_creatures) > 0.9: # 상대 있음, 종 유사도 0.9 초과
                        if self.energy > self.traits.all_initial_offspring_energy: # 상대 에너지 충분
                            return self.mate_breed(breed_creatures)
            elif self.energy > self.traits.all_initial_offspring_energy*2: # 무성생식에 에너지 충분
                    return self.self_breed()

        # 이동
        if (not self.move_speed) or (not self.traits.speed): return None

        return self.move()
        

    def move(self):
        new_position = Vector2(self.move_dir_x, self.move_dir_y)*self.traits.speed*self.move_speed + self.position
        self.energy -= self.move_speed * self.traits.move_cost
    
        if (new_position.x < 0 or 
            new_position.y < 0 or 
            new_position.x >= WORLD_WIDTH_SCALE*GRID_WIDTH_SCALE or 
            new_position.y >= WORLD_HIGHT_SCALE*GRID_HIGHT_SCALE): #TODO 임시. 차후 테두리는 생존 불가능 구역으로 설정하여 문제 해결.
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
            
    def self_breed(self):
        self.energy -= self.traits.all_initial_offspring_energy
        return [Creature(
                self.position+Vector2(
                np.cos(theta := np.random.uniform(0, 2 * np.pi)) * self.traits.size,
                np.sin(theta) * self.traits.size
            ), 
                self.genome.apply_mutation(list(self.genome.genome_bytes), self.traits.mutation_intensity), 
                self.world, 
                self.grid,
                self.traits.initial_offspring_energy) for _ in range(self.traits.offspring_count)]
    
    def mate_breed(self, partner:'Creature'):
        self.energy -= self.traits.all_initial_offspring_energy/2
        partner.energy -= self.traits.all_initial_offspring_energy/2

        return [Creature(
                self.position+Vector2(
                np.cos(theta := np.random.uniform(0, 2 * np.pi)) * self.traits.size,
                np.sin(theta) * self.traits.size
            ), 
                self.genome.crossover(partner.genome.genome_bytes, self.traits.mutation_intensity, self.traits.crossover_cut_number), 
                self.world, 
                self.grid,
                self.traits.initial_offspring_energy) for _ in range(self.traits.offspring_count)]
    

    def get_species_similarity(self, other: 'Creature') -> float:
        if other is self:
            return 1.0

        if other in self._similarity_cache:
            return self._similarity_cache[other]
        
        self_gene_str = self.genome.genome_bytes('utf-8', errors='ignore')
        other_gene_str = other.genome.genome_bytes('utf-8', errors='ignore')

        sim = gene_similarity(self_gene_str, other_gene_str)
        self._similarity_cache[other] = sim
        return sim

        
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