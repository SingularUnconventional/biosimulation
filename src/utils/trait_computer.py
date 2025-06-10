from src.utils.brain_constants import INPUT_INDICES, OUTPUT_INDICES
from src.utils.datatypes import Genes, Traits
from src.utils.constants import *
from src.utils.math_utils import filter_reachable_loads, intersect_lists

import numpy as np

def compute_biological_traits(genes:Genes) -> Traits:
    traits = Traits()

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

    food_intake_penalty = genes.intake_rates * FOOD_DIGESTION_COSTS[genes.food_intake]

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
    attack_cost         = BMR * ATTACK_COST_RATIO * attack_power
    attack_range        = (genes.limb_length_factor*ATTACK_RANGE_LIMB_RATIO+1) * genes.size
    
    retaliation_damage  = genes.size * genes.retaliation_damage_ratio

    # 이동 속도 계산
    speed               = SPEED_BASE * genes.limb_length_factor * ((genes.muscle_density / genes.size) ** SPEED_MASS_INFLUENCE)
    move_cost           = BMR * SPEED_COST_RATIO * speed

    # 수명 계산
    lifespan            = LIFESPAN_SCALE * (genes.size / BMR)

    # 에너지 저장량 계산
    energy_reserve = genes.size * (
        1 +
        genes.muscle_density * ENERGY_RESERVE_MUSCLE_MULTIPLIER +
        genes.skin_thickness * ENERGY_RESERVE_SKIN_MULTIPLIER
    ) * ENERGY_RESERVE_MULTIPLIER

    all_initial_offspring_energy = energy_reserve * genes.offspring_energy_share

    # 자식에게 줄 초기 에너지 계산
    initial_offspring_energy = all_initial_offspring_energy / genes.offspring_count

    # 시간당 에너지 섭취량 계산
    intake_rates = genes.intake_rates * genes.size * ENERGY_INTAKE_RATES[genes.food_intake]

    #실제 에너지 섭취량
    actual_intake = intake_rates * genes.digestive_efficiency

    #체력 회복량 계산
    recovery_rate = BMR * RECOVERY_RATE

    #군집 압력
    crowding_pressure = genes.size*CRUSH_DAMAGE_PER_SIZE

    #적합 지형
    preferred_altitude = 20-genes.preferred_altitude

    if genes.brain_synapses:
        #작동 뉴런 계산
        brain_synapses = filter_reachable_loads(INPUT_INDICES.keys(), OUTPUT_INDICES.keys(), genes.brain_synapses)

        if brain_synapses:
            arr = np.array(brain_synapses)
            brain_max_nodeInx = int(np.max(arr))

            #작동 입출력 뉴런

            input_keys_set = set(INPUT_INDICES.keys())
            output_keys_set = set(OUTPUT_INDICES.keys())

            brain_input_synapses = {
                key: INPUT_INDICES[key]
                for key in map(int, arr[:, 0])
                if key in input_keys_set
            }
            brain_output_synapses = {
                key: OUTPUT_INDICES[key]
                for key in map(int, arr[:, 0])
                if key in output_keys_set
            }

            brain_input_key_set = {v[0] for v in brain_input_synapses.values()}
            brain_output_key_set = {v[0] for v in brain_output_synapses.values()}

            traits.brain_max_nodeInx		   = brain_max_nodeInx
            traits.brain_input_synapses	   = brain_input_synapses
            traits.brain_output_synapses	   = brain_output_synapses
            traits.brain_input_key_set      = brain_input_key_set
            traits.brain_output_key_set     = brain_output_key_set
            traits.brain_synapses            = brain_synapses
        

    traits.size                      = genes.size
    traits.digestive_efficiency      = genes.digestive_efficiency
    traits.food_intake			   = genes.food_intake

    traits.visual_resolution         = genes.visual_resolution
    traits.auditory_range            = genes.auditory_range
    traits.visible_entities          = genes.visible_entities
    traits.can_locate_closest_food   = genes.can_locate_closest_food

    traits.brain_compute_cycles      = genes.brain_compute_cycles
    
    traits.crossover_cut_number      = genes.crossover_cut_number
    traits.mutation_intensity        = genes.mutation_intensity
    traits.reproductive_mode         = genes.reproductive_mode
    traits.calls                     = genes.calls
    traits.species_color_rgb         = genes.species_color_rgb
    traits.offspring_count           = genes.offspring_count

    traits.BMR                       = BMR
    traits.health                    = health
    traits.attack_range              = attack_range
    traits.attack_power              = attack_power
    traits.attack_cost               = attack_cost
    traits.move_cost                 = move_cost
    traits.retaliation_damage        = retaliation_damage
    traits.speed                     = speed
    traits.lifespan                  = lifespan
    traits.energy_reserve            = energy_reserve
    traits.all_initial_offspring_energy=all_initial_offspring_energy
    traits.initial_offspring_energy  = initial_offspring_energy
    traits.intake_rates			     = intake_rates
    traits.actual_intake			 = actual_intake
    traits.recovery_rate             = recovery_rate
    traits.crowding_pressure         = crowding_pressure
    traits.preferred_altitude        = preferred_altitude

    

    return traits