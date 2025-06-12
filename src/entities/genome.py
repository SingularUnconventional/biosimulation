import sys, os
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.datatypes    import Genes
from src.utils.constants    import *
from src.utils.math_utils   import apply_weight_or_default, apply_weight_or_default_int, list_apply_weight, list_apply_weight_and_pad, apply_weights_with_flag
    
import numpy as np

class Genome:
    # 속성 정의: (속성명, 데이터 형식, 가중치)
    # 데이터 형식:
    # 0 - 단일 값 (평균으로 갱신)
    # 1 - 리스트 값 (누적 또는 추가)
    # 2 - 중첩 리스트 값 (복잡한 구조 표현)
    GENE_DEFINITIONS = [
        (3, 'size',                        0, apply_weight_or_default_int,     (0.5, 1, 100000, 1)),
        (2, 'limb_length_factor',          0, apply_weight_or_default,     (0.0015, 0, 5)),
        (2, 'muscle_density',              0, apply_weight_or_default,     (0.0015, 0, 5)),
        (2, 'skin_thickness',              0, apply_weight_or_default,     (0.001, 0.1, 50, 0.01)),
        (2, 'attack_organ_power',          0, apply_weight_or_default,     (0.02, 0.1, 100)),
        (1, 'retaliation_damage_ratio',    0, apply_weight_or_default,     (0.002, 1, 5)),
        (2, 'food_intake',                 0, apply_weight_or_default_int, (0.0015, 0, 4)),
        (1, 'intake_rates',                0, apply_weight_or_default,     (0.001, 0.05, 1)),
        (1, 'digestive_efficiency',        0, apply_weight_or_default,     (0.001, 0.5, 1, 0.1)),

        (2, 'visual_resolution',           0, apply_weight_or_default_int, (0.002, 0, 4)),
        (1, 'auditory_range',              0, apply_weight_or_default_int, (0.005, 0, 4)),
        (1, 'visible_entities',            0, apply_weight_or_default_int, (0.05, 0, 500)),
        (1, 'can_locate_closest_food',     0, apply_weight_or_default_int, (0.001, 0, 1)),
        (2, 'preferred_altitude',          0, apply_weight_or_default_int, (0.005, 10, 20)),

        (95, 'brain_synapses',             2, apply_weights_with_flag,     ((1, 0.1, 1), (1000000, 10, 1000000), (0, -5, 0))),

        (1, 'brain_compute_cycles',        0, apply_weight_or_default_int, (0.01, 1, 1000)),
        (2, 'crossover_cut_number',        0, apply_weight_or_default_int, (0.05, 3, 500)),
        (1, 'mutation_intensity',          0, apply_weight_or_default,     (0.0002, 0.5, 1)),
        (1, 'reproductive_mode',           0, apply_weight_or_default_int, (0.001, 0, 1)),
        (2, 'calls',                       1, list_apply_weight_and_pad,   (1, 0, 999, CRY_VOLUME_SIZE)),
        (1, 'species_color_rgb',           1, list_apply_weight_and_pad,   (0.005, 0, 1, 6)),
        (1, 'offspring_energy_share',      0, apply_weight_or_default,     (0.002, 0.3, 0.5)),
        (1, 'offspring_count',             0, apply_weight_or_default_int, (0.0005, 2, 100, 1)),
    ]

    attribute_name_list = [
        (name, fmt)
        for repeat, name, fmt, *_  in GENE_DEFINITIONS
        for _ in range(repeat)
    ]

    def __init__(self, genome_bytes_bytes: bytes):
        self.genome_bytes = genome_bytes_bytes  # 유전자 시퀀스 (바이트열)
        # 속성 초기화: 형식에 따라 0 또는 빈 리스트
        self.attributes = {name : 0 if fmt == 0 else [] for _, name, fmt, *_ in self.GENE_DEFINITIONS}
        self.traits = None
        # 초기 선택 속성
        self.current_attr_index, self.data_format = self.attribute_name_list[0]
        self.parse_genome_bytes()
        self.finalize_attributes()

    def finalize_attributes(self):
        """최종적인 속성 정규화"""
        self.traits = Genes(*(
            genome_bytes_function(self.attributes[name],*index) 
            for _, name, _, genome_bytes_function, index in self.GENE_DEFINITIONS
        ))

    def parse_genome_bytes(self):
        """유전자 바이트열을 속성으로 변환"""
        for byte in self.genome_bytes:
            is_command = (byte >> 7) & 0b1       # 최상위 1비트: 명령 여부
            data = byte & 0b01111111             # 나머지 7비트: 데이터 값

            if is_command:
                self._set_current_attribute(data)   # 속성 전환
            else:
                self._accumulate_gene_data(data)    # 데이터 적용

    def _set_current_attribute(self, index):
        """속성 전환 명령 처리"""
        self.current_attr_index, self.data_format = self.attribute_name_list[index]
        attr = self.attributes[self.current_attr_index]

        # 포맷 1: 리스트일 경우 새로운 항목 초기화
        if self.data_format == 1 and (not attr or attr[-1] != 0):
            attr.append(0)
        # 포맷 2: 중첩 리스트일 경우 빈 리스트 추가
        elif self.data_format == 2:
            attr.append([])

    def _accumulate_gene_data(self, data):
        """현재 선택된 속성에 값 적용"""
        attr = self.attributes[self.current_attr_index]

        if self.data_format == 0:
            # 평균 방식으로 단일 값 누적
            self.attributes[self.current_attr_index] = attr + data

        elif self.data_format == 1:
            # 리스트 마지막 항목에 누적하거나 새로 추가
            if attr:
                attr[-1] += data
            else:
                attr.append(data)

        elif self.data_format == 2:
            # 중첩 리스트에 값 추가
            if not attr:
                attr.append([])
            attr[-1].append(data)

    def crossover(self, partner_genome_bytes: bytes, mutation_rate, num_cuts: int = 3) -> bytes:
        """다중 절단 교차 방식으로 자식 유전자 생성 (길이 패딩 없이)

        Args:
            partner_genome_bytes (Genome): 교차할 대상 Genome
            num_cuts (int): 절단 지점 개수

        Returns:
            Genome: 교차된 자식 Genome 객체
        """
        parent1 = list(self.genome_bytes)
        parent2 = list(partner_genome_bytes)
        min_len = min(len(parent1), len(parent2))

        # 절단 지점 생성
        if num_cuts >= min_len:
            num_cuts = max(1, min_len - 1)  # 과도한 절단 방지

        cut_points = sorted(np.random.choice(range(1, min_len), num_cuts, replace=False))
        cut_points = [0] + cut_points + [min_len]

        # 교차 조합
        child = []
        use_parent1 = True
        for i in range(len(cut_points) - 1):
            start, end = cut_points[i], cut_points[i + 1]
            source = parent1 if use_parent1 else parent2
            child.extend(source[start:end])
            use_parent1 = not use_parent1

        # 남은 바이트 붙이기 (랜덤한 부모 선택)
        child.extend(parent1[min_len:])

        return self.apply_mutation(child, mutation_rate)

    def apply_mutation(self, gene_sequence, mutation_rate):
        """유전자에 확률적으로 돌연변이 적용하여 새 바이트열 반환"""
        i = 0
        while i < len(gene_sequence):
            if np.random.random() < mutation_rate:
                mutation_type = np.random.choice([
                    "flip_bit",      # 임의의 비트 반전
                    "random_byte",   # 바이트 무작위 교체
                    "insert_byte",   # 바이트 삽입
                    "delete_byte"    # 바이트 삭제
                ])
                if mutation_type == "flip_bit":
                    bit = 1 << np.random.randint(0, 8)
                    gene_sequence[i] ^= bit
                elif mutation_type == "random_byte":
                    gene_sequence[i] = np.random.randint(0, 256)
                elif mutation_type == "insert_byte":
                    gene_sequence.insert(i, np.random.randint(0, 256))
                    i += 1  # 삽입된 바이트 건너뛰기
                elif mutation_type == "delete_byte" and len(gene_sequence) > 1:
                    del gene_sequence[i]
                    i -= 1  # 삭제 후 위치 보정
            i += 1
        return bytes(gene_sequence)



if __name__ == "__main__":
    
    GENOME_NUMBER = 200
    # 무작위 유전자 생성
    genome_bytess = [Genome(np.random.randint(0, 256, 1000, dtype=np.uint8).tobytes()) for _ in range(GENOME_NUMBER)]
    print("Parsed Genome:", genome_bytess[0].genome_bytes, "\nattributes:", genome_bytess[0].traits)

    count = 0
    
    endGenome = None
    searching = True
    
    while searching:
        # 돌연변이 유전자 생성
        genome_bytess = [Genome(genome_bytess[i].crossover(genome_bytess[i-np.random.randint(1, 10)])) for i in range(GENOME_NUMBER)]

        for genome_bytes in genome_bytess:
            for segment in genome_bytes.attributes['brain_synapses']: 
                if len(segment) >= 3:
                    if (segment[0] == 1 and segment[2] == 3) or (segment [0] == 3 and segment[2] == 1): 
                        searching = False
                        endGenome = genome_bytes

        count += 1
        print('count:', count, end='\r')

    print()
    print("genome_bytes:", endGenome.genome_bytes, "\nattributes:", endGenome.traits)