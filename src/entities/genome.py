import numpy as np

class Genome:
    # 속성 정의: 속성 인덱스 -> (속성명, 가중치)
    GENE_LIST = [
        ('asexual_reproduction', 1),
        ('edible_food_type',     1),
        ('size',                 0.1),
        ('base_metabolism',      0.01),
        ('stamina',              0.1),
        ('attack_power',         0.5),
        ('contact_attack_power', 0.5),
        ('sensory_complexity',   1),
        ('cry_complexity',       1),
        ('brain_structure',      1),
        ('max_speed',            0.1),
        ('lifespan',             0.5),
        ('brain_computation',    1)
    ]*10
    
    def __init__(self, genome_bytes: bytes):
        self.genome = genome_bytes
        self.attributes = {name: [] for name, _ in self.GENE_LIST}
        self.current_attr_index, _ = self.GENE_LIST[0]  # 초기 속성 인덱스
        self.parse_genome()

    def parse_genome(self):
        for byte in self.genome:
            cmd = (byte >> 6)   & 0b11      # 상위 2비트
            data=  byte         & 0b111111  # 하위 6비트

            
            if cmd == 0b10:  # 속성 전환
                if data >= len(self.GENE_LIST):
                    continue  # 유효하지 않은 속성 인덱스는 무시
                self.current_attr_index, _ = self.GENE_LIST[data]
                self.attributes[self.current_attr_index].append([])
            else:
                if self.attributes[self.current_attr_index]:
                    if cmd == 0b00:  # 누적
                        if self.attributes[self.current_attr_index][-1]:
                            self.attributes[self.current_attr_index][-1][-1] += data
                        else:
                            self.attributes[self.current_attr_index][-1].append(data)
                    elif cmd == 0b01:  # 새 값 추가
                        self.attributes[self.current_attr_index][-1].append(data)
                else:
                    self.attributes[self.current_attr_index].append([])
            # 0b11: 예약 (현재는 무시)

    def mutate(self, mutation_rate=0.01):
        """돌연변이를 적용한 새로운 Genome 객체를 반환"""
        genome_list = list(self.genome)

        i = 0
        while i < len(genome_list):
            if np.random.random() < mutation_rate:
                mutation_type = np.random.choice([
                    "flip_bit",      # 비트 반전
                    "random_byte",   # 비트 변경
                    "insert_byte",   # 비트 삽입
                    "delete_byte"    # 비트 제거
                ])

                if mutation_type == "flip_bit":
                    bit_to_flip = 1 << np.random.randint(0, 7)
                    genome_list[i] ^= bit_to_flip

                elif mutation_type == "random_byte":
                    genome_list[i] = np.random.randint(0, 255)

                elif mutation_type == "insert_byte":
                    genome_list.insert(i, np.random.randint(0, 255))
                    i += 1  # 방금 삽입된 바이트를 넘김

                elif mutation_type == "delete_byte" and len(genome_list) > 1:
                    del genome_list[i]
                    i -= 1  # 하나 삭제했으니 인덱스 유지

            i += 1

        mutated_bytes = bytes(genome_list)
        return mutated_bytes

    def __repr__(self):
        return f"<Genome {self.attributes}>"


if __name__ == "__main__":
    # 임의의 유전자 생성 (바이트 배열)
    genome_data = np.random.randint(0, 256, 100, dtype=np.uint8).tobytes()
    print(genome_data)
    genome = Genome(genome_data)
    print(genome)
    genome2 = Genome(genome.mutate(0.1))
    print(genome2)