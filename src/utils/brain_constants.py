from collections import defaultdict
from collections.abc import ValuesView

# === gene_index 생성 ===
def create_gene_index():
    gene_index = defaultdict(dict)

    # 단일 감각/행동 인자
    for name, idx in [
        ('food_pos_x', 0), ('food_pos_y', 1),
        ('move_speed_out', 2), ('move_y_out', 3), ('move_x_out', 4),
        ('attack_out', 18), ('reproduce_out', 19), ('eat_out', 20),
        ('focus_pos_x', 45), ('focus_pos_y', 46), ('focus_size', 47),
        ('focus_similarity', 110),      # 종 유사도
        ('focus_diet_type', 111),       # 초식/육식 경향
        ('focus_health', 112),          # 체력
        ('focus_color_saturation', 113),# HSV 중 S
        ('focus_color_hue', 114),       # HSV 중 H
        ('focus_hunger', 115),          # 허기
    ]:
        gene_index[name] = idx

    # 감지된 개체 정보 (단순 감지)
    gene_index['detected_pos_x'] = {i: 120 + (i - 1) * 37 for i in range(1, 51)}
    gene_index['detected_pos_y'] = {i: x + 1 for i, x in gene_index['detected_pos_x'].items()}
    gene_index['detected_size']  = {i: x + 2 for i, x in gene_index['detected_pos_x'].items()}

    # attention 대상 (선택적 주의 집중)
    attention_indices = [
        53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
        76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
        129, 130, 131, 132, 133, 134, 135, 136, 137, 138,
        166, 167, 168, 169, 170, 171, 172, 173, 174, 175,
        203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
        240, 241, 242, 243, 244, 245, 246, 247, 248, 249,
        277, 278, 279, 280, 281, 282, 283, 284, 285, 286,
        314, 315, 316, 317, 318, 319, 320, 321, 322, 323,
        351, 352, 353, 354, 355, 356, 357, 358, 359, 360,
        388, 389, 390, 391, 392, 393, 394, 395, 396, 397,
        425, 426, 427, 428, 429, 430, 431, 432, 433, 434,
        462, 463, 464, 465, 466, 467, 468, 469, 470, 471,
        499, 500, 501, 502, 503, 504, 505, 506, 507, 508,
        536, 537, 538, 539, 540, 541, 542, 543, 544, 545,
        573, 574, 575, 576, 577, 578, 579, 580, 581, 582,
        610, 611, 612, 613, 614, 615, 616, 617, 618, 619,
        647, 648, 649, 650, 651, 652, 653, 654, 655, 656,
        684, 685, 686, 687, 688, 689, 690, 691, 692, 693,
        721, 722, 723, 724, 725, 726, 727, 728, 729, 730,
        758, 759, 760, 761, 762, 763, 764, 765, 766, 767,
        795, 796, 797, 798, 799, 800, 801, 802, 803, 804,
        832, 833, 834, 835, 836, 837, 838, 839, 840, 841,
        869, 870, 871, 872, 873, 874, 875, 876, 877, 878,
        906, 907, 908, 909, 910, 911, 912, 913, 914, 915,
    ]
    gene_index['attention_selected'] = {i + 1: v for i, v in enumerate(attention_indices)}

    # 울음소리 듣기 (청각 감지)
    gene_index['audio_heard'] = {
        1: 26, 2: 27, 3: 28, 4: 29,
        5: 91, 6: 92, 7: 93, 8: 94
    }
    for i in range(9, 1001):
        block = (i - 9) // 4
        offset = (i - 9) % 4
        gene_index['audio_heard'][i] = 116 + block * 37 + 34 + offset

    # 울음소리 내기
    gene_index['cry_out'] = {
        1: 35, 2: 36, 3: 37, 4: 38, 5: 39,
        6: 100, 7: 101, 8: 102, 9: 103, 10: 104
    }

    return gene_index


GENE_INDEX = create_gene_index()

# 역추적용 인덱스 맵
INDEX_LOOKUP = {
    idx: (key, subkey)
    for key, val in GENE_INDEX.items()
    for subkey, idx in (
        val.items() if isinstance(val, dict) else
        ((None, v) for v in val) if isinstance(val, list) else
        [(None, val)]
    )
}

# 유틸: 다양한 value 타입을 평탄화
def flatten_gene_value(value):
    if isinstance(value, dict):
        return value.values()
    elif isinstance(value, (list, set, ValuesView)):
        return value
    else:
        return [value]
    
# 입력/출력 인덱스
INPUT_KEYS = [
    'food_pos_x', 'food_pos_y',
    'focus_pos_x', 'focus_pos_y', 'focus_size',
    'focus_similarity', 'focus_diet_type', 'focus_health',
    'focus_color_saturation', 'focus_color_hue', 'focus_hunger',
    'detected_pos_x', 'detected_pos_y', 'detected_size',
    'audio_heard'
]

OUTPUT_KEYS = [
    'move_speed_out', 'move_x_out', 'move_y_out',
    'attack_out', 'reproduce_out', 'eat_out', 'cry_out', 'attention_selected'
]

INPUT_INDICES = {idx: (key, ki) for key in INPUT_KEYS for ki, idx in enumerate(flatten_gene_value(GENE_INDEX[key]))}
OUTPUT_INDICES = {idx: (key, ki) for key in OUTPUT_KEYS for ki, idx in enumerate(flatten_gene_value(GENE_INDEX[key]))}


if __name__ == '__main__':
    #print(flatten_gene_value(GENE_INDEX['attention_selected']), len(OUTPUT_INDICES))
    print(GENE_INDEX['attention_selected'][2])
    print(sorted(list(INPUT_INDICES.keys())+ list(OUTPUT_INDICES.keys())))