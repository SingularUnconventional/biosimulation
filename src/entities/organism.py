from src.core.engine        import World
from src.utils.constants    import *
from src.utils.datatypes    import Color, Vector2
from src.utils.math_utils   import find_closest_point_arg, find_closest_point
from src.simulation.simulator import Simulator

import numpy as np

class Creature:
	def __init__(self, position : Vector2, world: World):
		self.world      : World     = world
		self.speciesId	: Color
		self.position	: Vector2 = position
		self.hp			: int
		self.maxEnergy	: int
		self.breedEnergy: int
		self.energy		: int
		self.speed		: float
		self.alive 		: bool = True

		self.set_value()
	
	def move(self):
		closestFood = self.world.foods[
		find_closest_point_arg(
			points=np.array([[food.position.x, food.position.y] for food in self.world.foods]),
			target=np.array([self.position.x, self.position.y])
		)]

		foodLocalPosX = closestFood.position.x - self.position.x
		foodLocalPosY = closestFood.position.y - self.position.y

		Scale = self.speed / (np.abs(foodLocalPosX) + np.abs(foodLocalPosY))

		self.position += Vector2(foodLocalPosX*Scale, foodLocalPosY*Scale)
		self.eat()

		if True: self.energy += SUBSTANCE_A_ENERGY
		self.energy -= CREATURE_BMR_ENERGY
		if self.energy < 0:
			self.alive = False


	def eat(self):
		foodLength, foodNum = find_closest_point(
			points=np.array([[food.position.x, food.position.y] for food in self.world.foods]),
			target=np.array([self.position.x, self.position.y])
		)

		food = self.world.foods[foodNum]

		if foodLength < 1:
			self.energy += food.energy
			food.regenerate()

	def set_value(self):
		self.speciesId 	= Color(np.random.randint(256), np.random.randint(256), np.random.randint(256))
		self.hp			= np.random.randint(CREATURE_MAX_HP/2, 	CREATURE_MAX_HP)
		self.maxEnergy	= np.random.randint(CREATURE_MAX_ENERGY/2,CREATURE_MAX_ENERGY)
		self.breedEnergy= np.random.randint(self.maxEnergy/2, 	self.maxEnergy)
		self.energy		= np.random.randint(self.maxEnergy/2, 	self.maxEnergy)
		self.speed		= np.random.uniform(CREATURE_MAX_SPEED/2,	CREATURE_MAX_SPEED)

	def breed(self):
		if self.energy > self.breedEnergy:
			...
			
#임시
class Food_:
	def __init__(self):
		self.position	: Vector2
		self.energy		: int = FOOD_START_ENERGY

	def regenerate(self):
		self.position = Vector2(
						np.random.uniform(WORLD_WIDTH_SCALE), 
					   	np.random.uniform(WORLD_HIGHT_SCALE))