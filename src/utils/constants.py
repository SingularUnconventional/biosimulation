#프로젝트 전반에서 사용하는 상수를 정의

GRID_WIDTH_SCALE   = 4000
GRID_HIGHT_SCALE   = 4000

WORLD_WIDTH_SCALE   = 100
WORLD_HIGHT_SCALE   = 100

CREATURES_SIZE      = 100

START_FOODS_SIZE	= 100
FOODS_SIZE      	= 1
FOOD_START_ENERGY	= 0.001

SUBSTANCE_A_ENERGY	= 0.0

NUM_ORGANIC         = 4
START_ORGANIC_RATES  = [1_000_000_000, 1_000_000_000, 1_000_000_000, 1_000_000_000]
#ORGANIC_GEN_RATE    = [0.1, 0.2, 0.3, 0.4]
#ORGANIC_MAX_AMOUNT  = [250, 500, 750, 1000]

ENERGY_INTAKE_RATES = [0.01, 20, 20, 20, 200]
DECAY_RETURN_ENERGY = [80, 80, 80, 80]

#지형에 따른 부식률 노이즈 생성.

# ======== 개체 상수 ========

# 대사량
BASAL_METABOLIC_CONSTANT        = 0.01  						# 기초 대사량 계수
BASAL_METABOLIC_EXPONENT        = 0.75							# 질량 대비 대사량 지수 (Kleiber's law 기반)
BASE_MULTIPLIER                 = 1.0							# BMR 기본 승수
FOOD_EFFICIENCY_BMR_MULTIPLIER  = 1.5					        # 소화 효율이 BMR에 미치는 영향
DIGESTIVE_EFFICIENCY_BASELINE   = 0.5						    # 소화 효율 기준값
FOOD_DIGESTION_COSTS            = [30, 30, 30, 30, 30]     # 음식 종류별 대사 비용 계수

# 감각 / 인지
BRAIN_ENERGY_COST               = 0.00005	# 뇌 시냅스 및 연산 비용
VISUAL_RESOLUTION_ENERGY_COST   = 0.03	    # 시각 해상도당 에너지 비용
AUDITORY_RANGE_ENERGY_COST      = 0.03		# 청각 반경당 에너지 비용
VISIBLE_ENTITY_ENERGY_COST      = 0.02		# 감지 가능한 생물 수당 비용
FOOD_LOCATION_ENERGY_COST       = 0.05		# 음식 위치 감지 여부에 따른 비용
THRESHOLD_WEIGHT                = 0.001     # 역치 가중인자

# 신체활동
LIMB_LENGTH_ENERGY_COST         = 20		# 팔다리 길이에 따른 비용
MUSCLE_DENSITY_ENERGY_COST      = 100	    # 근밀도에 따른 비용
SKIN_THICKNESS_ENERGY_COST      = 0.1	    # 피부 두께에 따른 비용
ATTACK_ORGAN_ENERGY_COST        = 0.015	    # 공격 기관 파괴력에 따른 비용

# 체력, 공격, 속도, 수명
BASE_HEALTH                     = 1000
SIZE_HEALTH_MULTIPLIER          = 2000
SKIN_HEALTH_MULTIPLIER          = 1000
ATTACK_RANGE_LIMB_RATIO         = 0.1
ATTACK_COST_RATIO               = 0.007
SPEED_COST_RATIO                = 0.00007
SPEED_BASE                      = 50
SPEED_MASS_INFLUENCE            = 0.4
LIFESPAN_SCALE                  = 20000.0

# 에너지 저장
ENERGY_RESERVE_MUSCLE_MULTIPLIER= 0.5      # 근밀도가 에너지 저장량에 미치는 영향
ENERGY_RESERVE_SKIN_MULTIPLIER  = 0.1      # 피부 두께가 에너지 저장량에 미치는 영향
ENERGY_RESERVE_MULTIPLIER       = 30000   # 전체적인 에너지 저장량


CRUSH_DAMAGE_PER_SIZE = 100  # 압사 데미지 계수
CRY_VOLUME_SIZE = 10 #한 개체가 낼 수 있는 소리 한계
RECOVERY_RATE = 1 #회복계수
ALTITUDE_HEALTH_DECAY = 0.1  # 고도 불일치 기본 감쇠율