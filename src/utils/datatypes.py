from dataclasses import dataclass

@dataclass
class Color:
	r : int #0-255
	g : int #0-255
	b : int #0-255

class Vector2:...
@dataclass
class Vector2:
	x : int
	y : int

	def __add__(self, vector : Vector2) -> Vector2:
		return Vector2(self.x + vector.x, self.y + vector.y)