#프로젝트 전반에서 사용하는 상수를 정의

WORLD_WIDTH_SCALE   = 40
WORLD_HIGHT_SCALE   = 40

CREATURES_SIZE		= 50
CREATURE_MAX_HP		= 200
CREATURE_MAX_ENERGY	= 200
CREATURE_MAX_SPEED	= 3
CREATURE_BMR_ENERGY	= 3

FOODS_SIZE			= 30
FOOD_START_ENERGY	= 30

SUBSTANCE_A_ENERGY	= 1


# ======== 개체 상수 ========
BASAL_METABOLISM_COEFF  = 10    # 기초대사량 상수 (J/s)
METABOLISM_EXPONENT     = 0.75  # Kleiber's Law 지수
HEALTH_PER_VOLUME       = 100   # 체력 계수 (HP/m³)
SPEED_SCALE_COEFF       = 2.5   # 속도 스케일 계수
VISION_RANGE_COEFF      = 5     # 시야 반경 계수
HEARING_RANGE_COEFF     = 4     # 청각 반경 계수
FOOD_SPEED_GROWTH_COEFF = 0.1   # 크기에 따른 섭취속도 증가 계수
MOVEMENT_ENERGY_COEFF   = 2     # 이동 에너지 계수 (J / m³·m/s)
BRAIN_ENERGY_PER_OP     = 0.05  # 연산당 에너지 소비량 (J)