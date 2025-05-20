from src.core.engine        import World
from src.entities.genome    import Genome
from src.utils.constants    import *
from src.utils.datatypes    import Color, Vector2, Genes, Traits
from src.utils.math_utils   import find_closest_point_arg, find_closest_point

import numpy as np


class Creature:
    def __init__(self, 
                 position       : Vector2, 
                 genome_bytes   : bytes, 
                 world          : World,
                 start_energy   : float,
                 ):
        self.genome = Genome(genome_bytes)
        self.traits = Traits(self.genome.traits)

        self.world          : World     = world
        self.position       : Vector2   = position
        self.health         : float     = self.traits.health
        self.energy         : float     = start_energy
        self.alive          : bool      = True
    
    def move(self):
        if self.world.foods:
            closestFood = self.world.foods[
            find_closest_point_arg(
                points=np.array([[food.position.x, food.position.y] for food in self.world.foods]),
                target=np.array([self.position.x, self.position.y])
            )]

            foodLocalPosX = closestFood.position.x - self.position.x
            foodLocalPosY = closestFood.position.y - self.position.y

            Scale = self.traits.speed / (np.abs(foodLocalPosX) + np.abs(foodLocalPosY))

            self.position += Vector2(foodLocalPosX*Scale, foodLocalPosY*Scale)
            self.eat()
        self.breed()

        if True: self.energy += SUBSTANCE_A_ENERGY*self.traits.food_intake_rates[0]
        self.energy -= self.traits.BMR
        if self.energy < 0:
            self.alive = False


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
        if self.energy > self.traits.initial_offspring_energy*self.traits.offspring_count*2:
            for _ in range(self.traits.offspring_count):
                self.world.creatures.append(Creature(
                    self.position+Vector2(np.random.random(), np.random.random()), 
                    self.genome.crossover(self.genome.genome_bytes, self.traits.mutation_intensity), 
                    self.world, 
                    self.traits.initial_offspring_energy))
            
            self.energy -= self.traits.initial_offspring_energy*self.traits.offspring_count
            
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