from src.entities.environment import OrganicMatterSource
from src.utils.datatypes    import Vector2, Traits, Genes
from src.utils.constants    import *
from src.utils.noise_fields	import generate_noise_field

import noise
import numpy as np

class World:
	def __init__(self):
		organics_noise = generate_noise_field(
			shape=(GRID_WIDTH_SCALE, GRID_HIGHT_SCALE),
			scale=1,
			seeds=[np.random.randint(100) for _ in range(NUM_ORGANIC)]
		)

		self.world = [[
			Grid(organics_noise[yGrid, xGrid])
			for xGrid in range(GRID_WIDTH_SCALE)]
			for yGrid in range(GRID_HIGHT_SCALE)
		]


		# from src.entities.organism import Creature
		# [Creature(Vector2(
		# 	np.random.uniform(WORLD_WIDTH_SCALE), 
		# 	np.random.uniform(WORLD_HIGHT_SCALE)
		# 	), np.random.randint(0, 256, 150, dtype=np.uint8).tobytes(), self, 0.1)
			
		# 	for _ in range(CREATURES_SIZE)]
			
			
	def Trun(self):
		
		# for creature in self.creatures:
		# 	creature.move()

		
		# self.foods += [self.Food() for _ in range(FOODS_SIZE)]

		# self.creatures = [creature for creature in self.creatures if creature.alive]

class Grid:
	def __init__(self, organic_affinity:list[float]):
		
		self.organics = OrganicMatterSource([(
			organic_affinity[i]*ORGANIC_GEN_RATE[i],
			organic_affinity[i]*ORGANIC_MAX_AMOUNT[i]) for i in range(NUM_ORGANIC)])
		
		self.creatures = []