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

		self.scNumber = 0
		self.passcount = 0
	def step(self):
		self.count +=1
		if self.count < self.passcount: 
			print(f"| {self.count}/{self.passcount} | {self.count/self.passcount*100:.1f}% {"="*int(self.count/self.passcount*50)}>{"-"*int((self.passcount-self.count)/self.passcount*50)}", end='\r')
			return
		import os
		os.system('clear')
		creatures = list(set().union(*[
			set().union(*[
				self.world.world[y][x].creatures 
				for x in range(WORLD_WIDTH_SCALE)]) 
				for y in range(WORLD_HIGHT_SCALE)]))
		
		
		# for i, creature in enumerate(creatures):
		# 	if creature.id == 11776:
		# 		self.scNumber = i

		print('Trun:', self.count, '\tsize:', len(creatures), '\tgeneS:', len(creatures[self.scNumber].genome.genome_bytes))
		print('%-25s' % 'id', creatures[self.scNumber].id)
		for name, trait in asdict(creatures[self.scNumber].traits).items():
			print('%-25s' % name, trait)
		print('%-25s' % 'energy', creatures[self.scNumber].energy)
		print('%-25s' % 'Pos', f"x={creatures[self.scNumber].position.x:.3f} y={creatures[self.scNumber].position.y:.3f}")
		print('%-25s' % 'GridPos', f"x={creatures[self.scNumber].grid.pos.x} y= {creatures[self.scNumber].grid.pos.y}")
		# for yGrid in self.world.world:
		# 	for Grid in yGrid:
		# 		print(f"{Grid.organics.current_amounts[0]:.0f}", end=' ')
		# 	print()
		commend = input()
		if commend:
			self.passcount = int(commend)

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