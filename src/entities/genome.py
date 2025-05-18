import numpy as np

import sys, os
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.math_utils import apply_weight_or_default, apply_weight_and_pad, apply_weights_with_flag

    
class Genome:
    # 속성 정의: (속성명, 데이터 형식, 가중치)
    # 데이터 형식:
    # 0 - 단일 값 (평균으로 갱신)
    # 1 - 리스트 값 (누적 또는 추가)
    # 2 - 중첩 리스트 값 (복잡한 구조 표현)
    GENE_DEFINITIONS = [
        ('asexual_reproduction', 0, apply_weight_or_default,    (1,      2)),
        ('edible_food_type',     0, apply_weight_or_default,    (1,      2)),
        ('size',                 0, apply_weight_or_default,    (0.1,   14)),
        ('base_metabolism',      0, apply_weight_or_default,    (0.01,   6)),
        ('stamina',              1, apply_weight_and_pad,       (0.3,    1,  4)),
        ('attack_power',         0, apply_weight_or_default,    (0.1,    7)),
        ('contact_attack_power', 0, apply_weight_or_default,    (1,      6.3)),
        ('sensory_complexity',   0, apply_weight_or_default,    (0.4,    5)),
        ('cry_complexity',       0, apply_weight_or_default,    (0.5,    1)),
        ('brain_structure',      1, apply_weight_and_pad,       (0.5,   18, 7)),
        ('max_speed',            0, apply_weight_or_default,    (1,      3.4)),
        ('lifespan',             0, apply_weight_or_default,    (0.1,    0.3)),
        ('brain_computation',    2, apply_weights_with_flag,    ((1, 0.1, 1),))
    ]  # 속성 반복 (확장용)

    def __init__(self, genome_bytes: bytes):
        self.genome = genome_bytes  # 유전자 시퀀스 (바이트열)
        # 속성 초기화: 형식에 따라 0 또는 빈 리스트
        self.attributes = {name: 0 if fmt == 0 else [] for name, fmt, _,_ in self.GENE_DEFINITIONS}
        self.final_attributes = {}
        # 초기 선택 속성
        self.current_attr_index, self.data_format, _,_ = self.GENE_DEFINITIONS[0]
        self.parse_genome()
        self.finalize_attributes()

    def finalize_attributes(self):
        """최종적인 속성 정규화"""
        self.final_attributes = {
            name: genome_function(self.attributes[name],*index) 
            for name, _, genome_function, index in self.GENE_DEFINITIONS
            }

    def parse_genome(self):
        """유전자 바이트열을 속성으로 변환"""
        for byte in self.genome:
            is_command = (byte >> 7) & 0b1       # 최상위 1비트: 명령 여부
            data = byte & 0b01111111             # 나머지 7비트: 데이터 값

            if is_command:
                self._set_current_attribute(data)   # 속성 전환
            else:
                self._accumulate_gene_data(data)    # 데이터 적용

    def _set_current_attribute(self, index):
        """속성 전환 명령 처리"""
        if index >= len(self.GENE_DEFINITIONS):
            return  # 유효하지 않은 인덱스 무시
        self.current_attr_index, self.data_format, _,_ = self.GENE_DEFINITIONS[index]
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
            self.attributes[self.current_attr_index] = (attr + data) / 2

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

    def crossover(self, partner_genome: 'Genome', num_cuts: int = 3) -> 'Genome':
        """다중 절단 교차 방식으로 자식 유전자 생성 (길이 패딩 없이)

        Args:
            partner_genome (Genome): 교차할 대상 Genome
            num_cuts (int): 절단 지점 개수

        Returns:
            Genome: 교차된 자식 Genome 객체
        """
        parent1 = list(self.genome)
        parent2 = list(partner_genome.genome)
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

        return self._apply_mutation(child)

    def _apply_mutation(self, gene_sequence, mutation_rate=0.01):
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
    genomes = [Genome(np.random.randint(0, 256, 100, dtype=np.uint8).tobytes()) for _ in range(GENOME_NUMBER)]
    print("Parsed Genome:", genomes[0].genome, "\nattributes:", genomes[0].final_attributes)

    count = 0
    
    endGenome = None
    searching = True
    
    while searching:
        # 돌연변이 유전자 생성
        genomes = [Genome(genomes[i].crossover(genomes[i-np.random.randint(1, 10)])) for i in range(GENOME_NUMBER)]

        for genome in genomes:
            for segment in genome.attributes['brain_computation']: 
                if len(segment) >= 3:
                    if (segment[0] == 1 and segment[2] == 3) or (segment [0] == 3 and segment[2] == 1): 
                        searching = False
                        endGenome = genome

        count += 1
        print('count:', count, end='\r')

    print()
    print("genome:", endGenome.genome, "\nattributes:", endGenome.final_attributes)