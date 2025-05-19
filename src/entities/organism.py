from src.core.engine        import World
from src.utils.constants    import *
from src.utils.datatypes    import Color, Vector2
from src.utils.math_utils   import find_closest_point_arg, find_closest_point

import numpy as np


# 생리적 계수 설정
def compute_biological_traits(genes):# 10,000,000
    size                    = genes['size']                     # 신체 크기 (kg) 0.01 ~ 100,000.0
    limb_length_factor      = genes['limb_length_factor']       # 팔다리 길이 계수 0.1 ~ 5.0
    muscle_density          = genes['muscle_density']           # 근밀도 계수 0.1 ~ 5.0
    skin_thickness          = genes['skin_thickness']           # 피부 두께 0.01 ~ 50.0
    attack_organ_power      = genes['attack_organ_power']       # 공격 기관의 파괴력 0.0 ~ 100.0
    retaliation_damage_ratio= genes['retaliation_damage_ratio'] # 반격 피해 비율 0.0 ~ 5.0
    food_intake_rates       = genes['food_intake_rates']        # 음식 종류별 시간당 섭취량 (list[float]) 0.0 ~ 10000.0    
    digestive_efficiency    = genes['digestive_efficiency']     # 섭취 에너지 변환율 0.1 ~ 1.0
    
    visual_resolution       = genes['visual_resolution']        # 시각 해상도(커질수록 상대의 정보 자세히 파악) 0 ~ 4
    auditory_range          = genes['auditory_range']           # 청각 감지 반경 (grid) 0 ~ 10
    visible_entities        = genes['visible_entities']         # 감지 가능한 생물 수 0 ~ 500
    can_locate_closest_food = genes['can_locate_closest_food']  # 가장 가까운 음식 인지 여부 (bool)
    
    brain_synapses          = genes['brain_synapses']           # 뇌 시냅스 리스트 0 ~ 1,000,000
    brain_compute_cycles    = genes['brain_compute_cycles']     # 뇌 연산 수행 횟수 (턴당) 0 ~ 1000
    
    mutation_intensity      = genes['mutation_intensity']       # 돌연변이 강도 0.0 ~ 1.0
    reproductive_mode       = genes['reproductive_mode']        # 생식 방식 (0: 무성, 1: 유성)
    calls                   = genes['calls']                    # 울음소리 리스트
    species_color_rgb       = genes['species_color_rgb']        # 종 유사도 표현 색상 (r, g, b)
    offspring_energy_share  = genes['offspring_energy_share']   # 자식에게 전해줄 초기 에너지 비율 0.0 ~ 0.5
    offspring_count         = genes['offspring_count']          # 한 번에 낳는 자식 수 1 ~ 100


    # --- BMR 계산 ---
    digestive_bonus = (digestive_efficiency - DIGESTIVE_EFFICIENCY_BASELINE) * FOOD_EFFICIENCY_BMR_MULTIPLIER
    brain_bonus     = len(brain_synapses)   * brain_compute_cycles * BRAIN_ENERGY_COST
    visual_bonus    = visual_resolution     * VISUAL_RESOLUTION_ENERGY_COST
    auditory_bonus  = auditory_range        * AUDITORY_RANGE_ENERGY_COST
    visibility_bonus= visible_entities      * VISIBLE_ENTITY_ENERGY_COST
    locating_bonus  =                         FOOD_LOCATION_ENERGY_COST if can_locate_closest_food else 0
    mobility_bonus  = limb_length_factor    * LIMB_LENGTH_ENERGY_COST + muscle_density * MUSCLE_DENSITY_ENERGY_COST
    skin_bonus      = skin_thickness        * SKIN_THICKNESS_ENERGY_COST
    attack_bonus    = attack_organ_power    * ATTACK_ORGAN_ENERGY_COST

    food_intake_penalty = sum(
        rate * FOOD_DIGESTION_COSTS[i] for i, rate in enumerate(food_intake_rates)
    )

    total_bmr_multiplier = BASE_MULTIPLIER + (
        digestive_bonus + brain_bonus + visual_bonus + auditory_bonus +
        visibility_bonus + locating_bonus + mobility_bonus + skin_bonus +
        attack_bonus + food_intake_penalty
    )

    BMR = BASAL_METABOLIC_CONSTANT * (size ** BASAL_METABOLIC_EXPONENT) * total_bmr_multiplier


    # 체력 계산
    health              = BASE_HEALTH + (SIZE_HEALTH_MULTIPLIER * size) + (SKIN_HEALTH_MULTIPLIER * skin_thickness)

    # 전투 계산
    attack_power        = (muscle_density + attack_organ_power) * size
    attack_cost         = BMR * ATTACK_COST_RATIO
    retaliation_damage  = size * retaliation_damage_ratio

    # 이동 속도 계산
    speed               = SPEED_BASE * limb_length_factor * ((muscle_density / size) ** SPEED_MASS_INFLUENCE)

    # 수명 계산
    lifespan            = LIFESPAN_SCALE * (size / BMR)

    # 에너지 저장량 계산
    energy_reserve = size * (
        1 +
        muscle_density * ENERGY_RESERVE_MUSCLE_MULTIPLIER +
        skin_thickness * ENERGY_RESERVE_SKIN_MULTIPLIER
    )

     # 자식에게 줄 초기 에너지 계산
    initial_offspring_energy = energy_reserve * offspring_energy_share / offspring_count

    return {
        # 유전적 표현형 정보
        "size"                      : size,
        "limb_length_factor"        : limb_length_factor,
        "muscle_density"            : muscle_density,
        "skin_thickness"            : skin_thickness,
        "attack_organ_power"        : attack_organ_power,
        "retaliation_damage"        : retaliation_damage,
        "digestive_efficiency"      : digestive_efficiency,
        "food_intake_rates"         : food_intake_rates,
        "visual_resolution"         : visual_resolution,
        "auditory_range"            : auditory_range,
        "visible_entities"          : visible_entities,
        "can_locate_closest_food"   : can_locate_closest_food,
        "brain_synapses"            : brain_synapses,
        "brain_compute_cycles"      : brain_compute_cycles,
        "mutation_intensity"        : mutation_intensity,
        "reproductive_mode"         : reproductive_mode,
        "calls"                     : calls,
        "species_color_rgb"         : species_color_rgb,
        "offspring_count"           : offspring_count,

        # 계산된 생물 특성
        "BMR"                       : BMR,
        "health"                    : health,
        "attack_power"              : attack_power,
        "attack_cost"               : attack_cost,
        "retaliation_damage"        : retaliation_damage,
        "speed"                     : speed,
        "lifespan"                  : lifespan,
        "energy_reserve"            : energy_reserve,
        "initial_offspring_energy"  : initial_offspring_energy,
    }


class Creature:
    def __init__(self, position : Vector2, world: World, genes:dict):
        self.world          : World = world
        self.speciesId      : Color
        self.position       : Vector2 = position
        self.hp             : int
        self.breedEnergy    : int
        self.energy         : int
        self.speed          : float
        self.alive          : bool = True
        
        #기본 생물 인자
        self.size                   : float = genes["size"]        
        self.limb_length_factor     : float = genes["limb_length_factor"]
        self.muscle_density         : float = genes["muscle_density"]
        self.skin_thickness         : float = genes["skin_thickness"]
        self.attack_organ_power     : float = genes["attack_organ_power"]
        self.retaliation_damage     : float = genes["retaliation_damage"]
        self.digestive_efficiency   : float = genes["digestive_efficiency"]
        self.food_intake_rates      : list  = genes["food_intake_rates"]
        self.visual_resolution      : int   = genes["visual_resolution"]
        self.auditory_range         : int   = genes["auditory_range"]
        self.visible_entities       : int   = genes["visible_entities"]
        self.can_locate_closest_food: int   = genes["can_locate_closest_food"]
        self.brain_synapses         : list  = genes["brain_synapses"]
        self.brain_compute_cycles   : int   = genes["brain_compute_cycles"]
        self.mutation_intensity     : float = genes["mutation_intensity"]
        self.reproductive_mode      : bool  = genes["reproductive_mode"]
        self.calls                  : list  = genes["calls"]
        self.species_color_rgb      : list  = genes["species_color_rgb"]
        self.offspring_count        : int   = genes["offspring_count"]
        
        self.BMR                    : float = genes["BMR"]
        self.health                 : float = genes["health"]
        self.attack_power           : float = genes["attack_power"]
        self.attack_cost            : float = genes["attack_cost"]
        self.retaliation_damage     : float = genes["retaliation_damage"]
        self.speed                  : float = genes["speed"]
        self.lifespan               : float = genes["lifespan"]
        self.energy_reserve         : float = genes["energy_reserve"]
        self.initial_offspring_energy:float = genes["initial_offspring_energy"]

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
        self.speciesId  = Color(np.random.randint(256), np.random.randint(256), np.random.randint(256))
        self.hp         = np.random.randint(CREATURE_MAX_HP/2,      CREATURE_MAX_HP)
        self.maxEnergy  = np.random.randint(CREATURE_MAX_ENERGY/2,  CREATURE_MAX_ENERGY)
        self.breedEnergy= np.random.randint(self.maxEnergy/2,       self.maxEnergy)
        self.energy     = np.random.randint(self.maxEnergy/2,       self.maxEnergy)
        self.speed      = np.random.uniform(CREATURE_MAX_SPEED/2,   CREATURE_MAX_SPEED)

    def breed(self):
        if self.energy > self.breedEnergy:
            ...
            
#임시
class Food_:
    def __init__(self):
        self.position    : Vector2
        self.energy      : int = FOOD_START_ENERGY

    def regenerate(self):
        self.position = Vector2(
                        np.random.uniform(WORLD_WIDTH_SCALE), 
                           np.random.uniform(WORLD_HIGHT_SCALE))