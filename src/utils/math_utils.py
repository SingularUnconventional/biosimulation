import numpy as np
import src.utils.datatypes as datatype

def find_closest_point_arg(points: np.array, target: np.array) -> int:
	dists = np.sum((points - target)**2, axis=1)
	return np.argmin(dists)

def find_closest_point(points: list[datatype.Vector2], target: datatype.Vector2):
	dists = np.sum((points - target)**2, axis=1)
	return np.min(dists), np.argmin(dists)
