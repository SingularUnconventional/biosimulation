from src.core.engine        import World
from src.utils.constants    import *
from dataclasses import asdict
class Viewer:
	def __init__(self, world : World):
		self.world = world
		self.count = 0
		self.texture = {
			"background": "  ",
			"block" 	: "⬜️",
			"food" 		: "🟩",
			"creature" 	: "🟦🟪⬜🟨🟧🟥",
		}

		self.creatureColorExpression = len(self.texture["creature"])-1

	def step(self):
		import os
		os.system('clear')
		print('Trun:', self.count, '\tsize:', len(self.world.creatures), '\tgeneS:', len(self.world.creatures[0].genome.genome_bytes))
		for name, trait in asdict(self.world.creatures[0].traits).items():
			print('%-25s' % name, trait)
		print('%-25s' % 'energy', self.world.creatures[0].energy)
		#input()
		self.count +=1
	def _step(self):
		print(self._printworld())
		print(self.texture["background"]*(WORLD_WIDTH_SCALE+2), end='\r')
		commend = input()

		print("\033[F"*(WORLD_HIGHT_SCALE+4))

		if commend != '':
			print(self.texture["background"]*(WORLD_WIDTH_SCALE+2), end='\r')
			try:
				print(commend)
				print(self.texture["background"]*(WORLD_WIDTH_SCALE+2), end='\r')
				print(eval(commend))
			except Exception as e:
				print("\033[31mfailed:", e, "\033[0m")
		
		
	def _printworld(self):
		grid = [[self.texture["background"]
				for _ in range(WORLD_WIDTH_SCALE)]
				for _ in range(WORLD_HIGHT_SCALE)]
		
		for creature in self.world.creatures:
			yPos = int(creature.position.y % WORLD_HIGHT_SCALE)
			xPos = int(creature.position.x % WORLD_WIDTH_SCALE)
			
			grid[yPos][xPos] = self.texture["creature"][int((self.creatureColorExpression*creature.energy)/(creature.energy+1000))]

		for food in self.world.foods:
			yPos = int(food.position.y)
			xPos = int(food.position.x)
			
			grid[yPos][xPos] = self.texture["food"]

		return self.texture["block"]*(WORLD_WIDTH_SCALE+2)+"\n"+"\n".join([self.texture["block"] + "".join(x_line) + self.texture["block"] for x_line in grid])+"\n"+self.texture["block"]*(WORLD_WIDTH_SCALE+2)