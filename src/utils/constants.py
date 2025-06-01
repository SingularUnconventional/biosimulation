#프로젝트 전반에서 사용하는 상수를 정의

GRID_WIDTH_SCALE   = 400
GRID_HIGHT_SCALE   = 400

WORLD_WIDTH_SCALE   = 100
WORLD_HIGHT_SCALE   = 100

CREATURES_SIZE      = 100

START_FOODS_SIZE	= 100
FOODS_SIZE      	= 1
FOOD_START_ENERGY	= 0.001

SUBSTANCE_A_ENERGY	= 0.0

NUM_ORGANIC         = 4
ORGANIC_GEN_RATE    = [0.1, 0.2, 0.3, 0.4]
ORGANIC_MAX_AMOUNT  = [250, 500, 750, 1000]

# ======== 개체 상수 ========

# 대사량
BASAL_METABOLIC_CONSTANT        = 0.01  						# 기초 대사량 계수
BASAL_METABOLIC_EXPONENT        = 0.75							# 질량 대비 대사량 지수 (Kleiber's law 기반)
BASE_MULTIPLIER                 = 1.0							# BMR 기본 승수
FOOD_EFFICIENCY_BMR_MULTIPLIER  = 1.5					        # 소화 효율이 BMR에 미치는 영향
DIGESTIVE_EFFICIENCY_BASELINE   = 0.5						    # 소화 효율 기준값
FOOD_DIGESTION_COSTS            = [80, 80, 80, 80, 80]     # 음식 종류별 대사 비용 계수

# 감각 / 인지
BRAIN_ENERGY_COST               = 0.00005	# 뇌 시냅스 및 연산 비용
VISUAL_RESOLUTION_ENERGY_COST   = 0.03	    # 시각 해상도당 에너지 비용
AUDITORY_RANGE_ENERGY_COST      = 0.03		# 청각 반경당 에너지 비용
VISIBLE_ENTITY_ENERGY_COST      = 0.02		# 감지 가능한 생물 수당 비용
FOOD_LOCATION_ENERGY_COST       = 0.05		# 음식 위치 감지 여부에 따른 비용

# 신체활동
LIMB_LENGTH_ENERGY_COST         = 0.1		# 팔다리 길이에 따른 비용
MUSCLE_DENSITY_ENERGY_COST      = 0.5	    # 근밀도에 따른 비용
SKIN_THICKNESS_ENERGY_COST      = 0.1	    # 피부 두께에 따른 비용
ATTACK_ORGAN_ENERGY_COST        = 0.015	    # 공격 기관 파괴력에 따른 비용

# 체력, 공격, 속도, 수명
BASE_HEALTH                     = 100.0
SIZE_HEALTH_MULTIPLIER          = 2.0
SKIN_HEALTH_MULTIPLIER          = 10.0
ATTACK_COST_RATIO               = 0.007
SPEED_BASE                      = 1.0
SPEED_MASS_INFLUENCE            = 0.4
LIFESPAN_SCALE                  = 20.0

# 에너지 저장
ENERGY_RESERVE_MUSCLE_MULTIPLIER= 0.5      # 근밀도가 에너지 저장량에 미치는 영향
ENERGY_RESERVE_SKIN_MULTIPLIER  = 0.1      # 피부 두께가 에너지 저장량에 미치는 영향
ENERGY_RESERVE_MULTIPLIER       = 10       # 전체적인 에너지 저장량
