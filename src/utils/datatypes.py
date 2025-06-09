
from src.utils.constants import *
from dataclasses import dataclass

#바이러스 특징
#높은 에너지 효율
#높은 번식력
#태양 에너지를 기반으로 한 무한한 에너지 공급

@dataclass
class Color:
	r : int #0-255
	g : int #0-255
	b : int #0-255

#class Vector2:...
@dataclass
class Vector2:
	x : int
	y : int

	def __add__(self, vector : 'Vector2') -> 'Vector2':
		return Vector2(self.x + vector.x, self.y + vector.y)
	
	def __sub__(self, other: 'Vector2') -> 'Vector2':
		return Vector2(self.x - other.x, self.y - other.y)
	
	def __mul__(self, other):
		return Vector2(self.x*other, self.y*other)
	
	def distance_sq(self, other: 'Vector2') -> int:
		dx = self.x - other.x
		dy = self.y - other.y
		return dx * dx + dy * dy
	

@dataclass
class Genes:
	size 					: float			# 0.01 ~ 100,000.0	신체 크기 (kg)
	limb_length_factor 		: float			# 0.1 ~ 5.0			팔다리 길이 계수 
	muscle_density 			: float			# 0.1 ~ 5.0			근밀도 계수 
	skin_thickness 			: float			# 0.01 ~ 50.0		피부 두께 
	attack_organ_power 		: float			# 0.0 ~ 100.0		공격 기관의 파괴력 
	retaliation_damage_ratio: float			# 0.0 ~ 5.0			반격 피해 비율 
	food_intake 			: int			# 0 ~ 4				섭취 가능 음식  
	intake_rates 			: float			# 0.0 ~ 10000.0		시간당 음식 섭취량
	digestive_efficiency 	: float			# 0.1 ~ 1.0			섭취 에너지 변환율 

	visual_resolution 		: int			# 0 ~ 4				시각 해상도(커질수록 상대의 정보 자세히 파악) 
	auditory_range 			: int			# 0 ~ 10			청각 감지 반경 (grid) 
	visible_entities 		: int			# 0 ~ 500			감지 가능한 생물 수 
	can_locate_closest_food : bool			# 0/1				가장 가까운 음식 인지 여부

	brain_synapses 			: list[list]	# 					뇌 시냅스 리스트 
	brain_compute_cycles 	: int			# 0 ~ 1000			뇌 연산 수행 횟수 (턴당)	
	
	mutation_intensity 		: float			# 0.0 ~ 1.0			돌연변이 강도 
	reproductive_mode 		: bool			# 					생식 방식 (0: 무성, 1: 유성)
	calls 					: list[int]		# 					울음소리 리스트
	species_color_rgb 		: list[int]		# 					종 유사도 표현 색상 (r, g, b)
	offspring_energy_share 	: int			# 0.0 ~ 0.5			자식에게 전해줄 초기 에너지 비율 
	offspring_count 		: int			# 1 ~ 100			한 번에 낳는 자식 수 

@dataclass
class Traits:
	size 					: float			= None # 0.01 ~ 100,000.0	신체 크기 (kg)
	food_intake				: int			= None # 0 ~ 4				섭취 가능 음식
	digestive_efficiency 	: float			= None # 0.1 ~ 1.0			섭취 에너지 변환율

	visual_resolution 		: int			= None # 0 ~ 4				시각 해상도(커질수록 상대의 정보 자세히 파악) 
	auditory_range 			: int			= None # 0 ~ 10				청각 감지 반경 (grid) 
	visible_entities 		: int			= None # 0 ~ 500			감지 가능한 생물 수 
	can_locate_closest_food : bool			= None # 0/1				가장 가까운 음식 인지 여부

	brain_compute_cycles 	: int			= None # 0 ~ 1000			뇌 연산 수행 횟수 (턴당)	
	
	mutation_intensity 		: float			= None # 0.0 ~ 1.0			돌연변이 강도 
	reproductive_mode 		: bool			= None # 					생식 방식 (0: 무성, 1: 유성)
	calls 					: list[int]		= None # 					울음소리 리스트
	species_color_rgb 		: list[int]		= None # 					종 유사도 표현 색상 (r, g, b)
	offspring_count 		: int			= None # 1 ~ 100			한 번에 낳는 자식 수 

	BMR						: float			= None
	health					: float			= None
	attack_power			: float			= None
	attack_cost				: float			= None
	move_cost				: float			= None
	retaliation_damage		: float			= None
	speed					: float			= None
	lifespan				: float			= None
	energy_reserve			: float			= None
	initial_offspring_energy: float			= None
	intake_rates 			: float			= None	# 0.0 ~ 10000.0		시간당 음식 섭취량     
	actual_intake			: float			= None
	brain_synapses 			: list[list]	= None # 					뇌 시냅스 리스트 
	brain_max_nodeInx		: int			= None
	brain_input_synapses	: list[int]   	= None
	brain_output_synapses	: list[int]   	= None
	brain_input_key_set		: set			= None
	brain_output_key_set	: set			= None