from src.entities.environment import OrganicMatterSource
from src.utils.datatypes    import Vector2, Traits, Genes
from src.utils.constants    import *

import noise
import numpy as np

class World:
	def __init__(self):
		...
			
	def Trun(self):
		for creature in self.creatures:
			creature.move()

		
		self.foods += [self.Food() for _ in range(FOODS_SIZE)]

		self.creatures = [creature for creature in self.creatures if creature.alive]

class Grid:
	def __init__(self, organic_affinity:list[float]):
		from src.entities.organism import Creature
		
		self.organics = OrganicMatterSource([(
			organic_affinity*ORGANIC_GEN_RATE[i], 
			organic_affinity*ORGANIC_MAX_AMOUNT[i]) for i in range(NUM_ORGANIC)])
		
		self.creatures = [Creature(Vector2(
							np.random.uniform(WORLD_WIDTH_SCALE), 
							np.random.uniform(WORLD_HIGHT_SCALE)
							), np.random.randint(0, 256, 150, dtype=np.uint8).tobytes(), self, 0.1)
							
							for _ in range(CREATURES_SIZE)]