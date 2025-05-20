from src.utils.constants import *

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
	size 					: float			# 0.01 ~ 100,000.0	신체 크기 (kg)
	limb_length_factor 		: float			# 0.1 ~ 5.0			팔다리 길이 계수 
	muscle_density 			: float			# 0.1 ~ 5.0			근밀도 계수 
	skin_thickness 			: float			# 0.01 ~ 50.0		피부 두께 
	attack_organ_power 		: float			# 0.0 ~ 100.0		공격 기관의 파괴력 
	retaliation_damage_ratio: float			# 0.0 ~ 5.0			반격 피해 비율 
	food_intake_rates 		: list[float]	# 0.0 ~ 10000.0		음식 종류별 시간당 섭취량     
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
	size 					: float			# 0.01 ~ 100,000.0	신체 크기 (kg)
	food_intake_rates 		: list[float]	# 0.0 ~ 10000.0		음식 종류별 시간당 섭취량     
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
	offspring_count 		: int			# 1 ~ 100			한 번에 낳는 자식 수 

	BMR						: float
	health					: float
	attack_power			: float
	attack_cost				: float
	retaliation_damage		: float
	speed					: float
	lifespan				: float
	energy_reserve			: float
	initial_offspring_energy: float


	def __init__(self, genes:Genes):
		self.compute_biological_traits(genes)

	# 생리적 계수 설정
	def compute_biological_traits(self, genes:Genes):# 10,000,000
		# --- BMR 계산 ---
		digestive_bonus = (genes.digestive_efficiency - DIGESTIVE_EFFICIENCY_BASELINE) * FOOD_EFFICIENCY_BMR_MULTIPLIER
		brain_bonus     = len(genes.brain_synapses)   * genes.brain_compute_cycles * BRAIN_ENERGY_COST
		visual_bonus    = genes.visual_resolution     * VISUAL_RESOLUTION_ENERGY_COST
		auditory_bonus  = genes.auditory_range        * AUDITORY_RANGE_ENERGY_COST
		visibility_bonus= genes.visible_entities      * VISIBLE_ENTITY_ENERGY_COST
		locating_bonus  =                         FOOD_LOCATION_ENERGY_COST if genes.can_locate_closest_food else 0
		mobility_bonus  = genes.limb_length_factor    * LIMB_LENGTH_ENERGY_COST + genes.muscle_density * MUSCLE_DENSITY_ENERGY_COST
		skin_bonus      = genes.skin_thickness        * SKIN_THICKNESS_ENERGY_COST
		attack_bonus    = genes.attack_organ_power    * ATTACK_ORGAN_ENERGY_COST

		food_intake_penalty = sum(
			rate * FOOD_DIGESTION_COSTS[i] for i, rate in enumerate(genes.food_intake_rates)
		)

		total_bmr_multiplier = BASE_MULTIPLIER + (
			digestive_bonus + brain_bonus + visual_bonus + auditory_bonus +
			visibility_bonus + locating_bonus + mobility_bonus + skin_bonus +
			attack_bonus + food_intake_penalty
		)

		BMR = BASAL_METABOLIC_CONSTANT * (genes.size ** BASAL_METABOLIC_EXPONENT) * total_bmr_multiplier


		# 체력 계산
		health              = BASE_HEALTH + (SIZE_HEALTH_MULTIPLIER * genes.size) + (SKIN_HEALTH_MULTIPLIER * genes.skin_thickness)

		# 전투 계산
		attack_power        = (genes.muscle_density + genes.attack_organ_power) * genes.size
		attack_cost         = BMR * ATTACK_COST_RATIO
		retaliation_damage  = genes.size * genes.retaliation_damage_ratio

		# 이동 속도 계산
		speed               = SPEED_BASE * genes.limb_length_factor * ((genes.muscle_density / genes.size) ** SPEED_MASS_INFLUENCE)

		# 수명 계산
		lifespan            = LIFESPAN_SCALE * (genes.size / BMR)

		# 에너지 저장량 계산
		energy_reserve = genes.size * (
			1 +
			genes.muscle_density * ENERGY_RESERVE_MUSCLE_MULTIPLIER +
			genes.skin_thickness * ENERGY_RESERVE_SKIN_MULTIPLIER
		)

		# 자식에게 줄 초기 에너지 계산
		initial_offspring_energy = energy_reserve * genes.offspring_energy_share / genes.offspring_count

		self.size                      = genes.size
		self.food_intake_rates         = genes.food_intake_rates
		self.digestive_efficiency      = genes.digestive_efficiency

		self.visual_resolution         = genes.visual_resolution
		self.auditory_range            = genes.auditory_range
		self.visible_entities          = genes.visible_entities
		self.can_locate_closest_food   = genes.can_locate_closest_food

		self.brain_synapses            = genes.brain_synapses
		self.brain_compute_cycles      = genes.brain_compute_cycles
		
		self.mutation_intensity        = genes.mutation_intensity
		self.reproductive_mode         = genes.reproductive_mode
		self.calls                     = genes.calls
		self.species_color_rgb         = genes.species_color_rgb
		self.offspring_count           = genes.offspring_count

		self.BMR                       = BMR
		self.health                    = health
		self.attack_power              = attack_power
		self.attack_cost               = attack_cost
		self.retaliation_damage        = retaliation_damage
		self.speed                     = speed
		self.lifespan                  = lifespan
		self.energy_reserve            = energy_reserve
		self.initial_offspring_energy  = initial_offspring_energy
