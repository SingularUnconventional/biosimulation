from src.utils.datatypes    import Vector2
from src.utils.constants    import *

import numpy as np

class World:
	def __init__(self):
		from src.entities.organism  import Creature, Food_

		self.creatures: list[Creature]= []
		self.foods 	: list[Food_] 	= []

		for _ in range(CREATURES_SIZE):
			creature = Creature(Vector2(
							np.random.uniform(WORLD_WIDTH_SCALE), 
							np.random.uniform(WORLD_HIGHT_SCALE)
							), self)
			
			self.creatures.append(creature)
		
		for _ in range(FOODS_SIZE):
			food = Food_()
			food.regenerate()

			self.foods.append(food)
			
	def Trun(self):
		for creature in self.creatures:
			creature.move()

		self.creatures = [creature for creature in self.creatures if creature.alive]
