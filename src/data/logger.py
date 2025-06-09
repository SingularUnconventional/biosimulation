import os
import json
import base64
import zstandard as zstd
from dataclasses import asdict
import numpy as np

from src.utils.creature_sprite_tool import generate_creature_sheet, reset_creature_sheet

class WorldLog:
    def __init__(self, grid_array, log_dir="logs", flush_interval=100):
        self.grid_array = grid_array
        self.turn_count = 0
        self.flush_interval = flush_interval

        self.log_dir = log_dir
        self.raw_log_file = os.path.join(self.log_dir, "turn_logs.jsonl")
        self.static_file = os.path.join(self.log_dir, "static_data.jsonl")
        self.offsets_file = os.path.join(self.log_dir, "offsets.bin")
        self.compressed_dir = os.path.join(self.log_dir, "compressed")
        self.index_path = os.path.join(self.compressed_dir, "index.jsonl")
        os.makedirs(self.compressed_dir, exist_ok=True)

        open(self.raw_log_file, "w").close()
        open(self.static_file, "w").close()
        open(self.index_path, "w").close()
        open(self.offsets_file, "wb").close()

        self.static_creature_data = []

        reset_creature_sheet()

    def register_creature(self, creatures):
        """새로운 생물체의 유전자 정보를 누적"""
        self.static_creature_data.extend([
            base64.b64encode(creature.genome.genome_bytes).decode('utf-8')
            for creature in creatures
        ])

    def write_static_data(self):
        """누적된 유전자 정보를 static_data.jsonl에 append하고, offsets.bin에도 오프셋 기록"""
        generate_creature_sheet(lines=self.static_creature_data)

        if self.static_creature_data:
            with open(self.static_file, "a", encoding="utf-8") as f_data, \
                open(self.offsets_file, "ab") as f_offset:

                for genome_str in self.static_creature_data:
                    # 현재 오프셋 저장 (byte 위치)
                    offset = f_data.tell()
                    f_offset.write(offset.to_bytes(8, byteorder="little"))

                    # 유전자 데이터 한 줄로 기록
                    f_data.write(json.dumps(genome_str) + "\n")

            self.static_creature_data.clear()

    def fast_round_scalar(self, v: float, scale: int = 10000) -> float:
        return int(v * scale) / scale
    
    def fast_round_array(self, v_array: np.ndarray, scale: int = 10000) -> np.ndarray:
        return np.floor(v_array * scale + 0.5) / scale

    def log_turn(self):
        """매 턴마다 로그를 기록 (리스트 기반 구조)"""
        turn_log = [
            self.turn_count,  # turn number
            [  # grids
                [  # each row
                    [  # each grid: [organics, creatures]
                        [self.fast_round_scalar(v) for v in grid.organics],  # [float]
                        [  # creatures
                            [  # each creature: [id, x, y, health, energy]
                                creature.id,
                                self.fast_round_scalar(creature.position.x),
                                self.fast_round_scalar(creature.position.y),
                                self.fast_round_scalar(creature.health),
                                self.fast_round_scalar(creature.energy),
                                self.fast_round_array(creature.brain_nodes).tolist()
                            ] for creature in grid.creatures
                        ],
                        [   #corpses
                            [  # each creature: [x, y, energy]
                                self.fast_round_scalar(corpse.position.x),
                                self.fast_round_scalar(corpse.position.y),
                                self.fast_round_scalar(corpse.energy)
                            ] for corpse in grid.corpses
                        ]
                    ] for grid in row
                ] for row in self.grid_array
            ]
        ]

        with open(self.raw_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn_log, separators=(",", ":")) + "\n")

        self.turn_count += 1

        if self.turn_count % self.flush_interval == 0:
            self.write_static_data()
            self.compress_log()

    def compress_log(self):
        """로그 파일 압축"""
        filename = f"turn_logs_{self.turn_count:08d}.zst"
        compressed_file = os.path.join(self.compressed_dir, filename)

        # 압축 수행
        cctx = zstd.ZstdCompressor(level=5)
        with open(self.raw_log_file, "rb") as in_f, open(compressed_file, "wb") as out_f:
            out_f.write(cctx.compress(in_f.read()))

        # 원본 로그 초기화
        open(self.raw_log_file, "w").close()

        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(filename) + "\n")

    def decompress_zstd_file(file_path: str) -> bytes:
        """Zstandard 압축 파일을 해제하여 원본 바이트 데이터를 반환"""
        try:
            with open(file_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                return dctx.decompress(f.read())
        except Exception as e:
            print(f"[Decompress Error] {file_path}: {e}")
            return b''
        
        