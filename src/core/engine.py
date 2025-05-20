from src.utils.datatypes    import Vector2, Traits, Genes
from src.utils.constants    import *

import numpy as np

class World:
	def __init__(self):
		from src.entities.organism  import Creature, Food_

		self.Food = Food_

		self.creatures: list[Creature]= []
		self.foods 	: list[Food_] 	= []

		for _ in range(CREATURES_SIZE):
			creature = Creature(Vector2(
							np.random.uniform(WORLD_WIDTH_SCALE), 
							np.random.uniform(WORLD_HIGHT_SCALE)
							), np.random.randint(0, 256, 150, dtype=np.uint8).tobytes(), self, 1)
			
			self.creatures.append(creature)
		
		for _ in range(FOODS_SIZE):
			self.foods.append(self.Food())
			
	def Trun(self):
		for creature in self.creatures:
			creature.move()

		
		self.foods += [self.Food() for _ in range(100)]

		self.creatures = [creature for creature in self.creatures if creature.alive]
