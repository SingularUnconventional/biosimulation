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
	

@dataclass
class Genes:
	size 					: 
	limb_length_factor 		: 
	muscle_density 			: 
	skin_thickness 			: 
	attack_organ_power 		: 
	retaliation_damage_ratio: 
	food_intake_rates 		: 
	digestive_efficiency 	: 
	visual_resolution 		: 
	auditory_range 			: 
	visible_entities 		: 
	can_locate_closest_food : 
	brain_synapses 			: 
	brain_compute_cycles 	: 
	mutation_intensity 		: 
	reproductive_mode 		: 
	calls 					: 
	species_color_rgb 		: 
	offspring_energy_share 	: 
	offspring_count 		: 