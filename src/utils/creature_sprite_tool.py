import sys
import os
import math
import base64
import json
import colorsys
import numpy as np
from PIL import Image
from dataclasses import asdict
from itertools import product

# === 상위 폴더 import 경로 추가 ===
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(PARENT_DIR)
from src.entities.genome import Genome

# === 상수 설정 ===
TILE_SIZE = 16
SPRITE_PATH = "assets\parts_template_16x16.png"
STATIC_PATH = "logs/static_data.jsonl"
IMAGE_PATH   = "logs/creature_sheet.png"

OFFSET_Y = TILE_SIZE // 2

# === 파츠 위치 상수 (단위: 픽셀) ===
BODY_Y = 0
LEGS_Y = 1
MOUTH_Y = 9
TAIL_Y = 10
EYE_X_BASE = 9
EYE_X_STRIDE = 7
EYE_Y_OFFSET = 6
ANTENNA_X = 16
ANTENNA_Y = 7

# === 파츠 인덱스 범위 ===
PART_RANGES = {
    'body': 7,
    'xlegs': 4,
    'ylegs': 4,
    'mouth': 8,
    'tail': 2,
    'eye_index': 3,
    'eye_variant': 5,
    'antenna': 6,
}

# === 타일 색상 변환 ===
def colorize_tile(tile, hue=0.0, sat=1.0):
    tile = tile.convert("RGBA")
    new_data = []
    for r, g, b, a in tile.getdata():
        if a == 0:
            new_data.append((0, 0, 0, 0))
        else:
            v = r / 255.0
            r_, g_, b_ = colorsys.hsv_to_rgb(hue, sat, v)
            new_data.append((int(r_ * 255), int(g_ * 255), int(b_ * 255), a))
    result = Image.new("RGBA", tile.size)
    result.putdata(new_data)
    return result

# === 타일 자르기 + 색상 적용 + 캔버스에 붙이기 ===
def paste_tile(canvas, sheet, x, y, w, h, hue_sat=None):
    tile = sheet.crop((x, y, x + w, y + h))
    if hue_sat:
        tile = colorize_tile(tile, *hue_sat)
    canvas.paste(tile, (0, OFFSET_Y), tile.split()[3])

# === 파츠 인덱스 매핑 ===
def map_gene_to_parts(gene):
    return {
        'body': min(int(math.log10(max(gene['size'], 1))), 6),
        'xlegs': int((gene['muscle_density'] - 0.1) / (5.0 - 0.1) * 3.999),
        'ylegs': int((gene['limb_length_factor'] - 0.1) / (5.0 - 0.1) * 3.999),
        'mouth': gene['food_intake'] if gene['food_intake'] < 4 else 4 + int(gene['attack_organ_power'] / 100 * 3.999),
        'tail': gene['reproductive_mode'],
        'eye_index': int(gene['visible_entities'] / 500 * 2.999),
        'eye_y': min(gene['visual_resolution'], 4),
        'antenna': int(gene['auditory_range'] / 10 * 5.999),
    }

# === 개체 이미지 생성 ===
def generate_creature_image(sprite_path, body, xlegs, ylegs, mouth, tail, eye_index, eye_y, antenna,
                            leg_color=(0.0, 1.0), body_color=(0.0, 1.0), antenna_color=(0.0, 1.0)):
    sheet = Image.open(sprite_path).convert("RGBA")
    canvas = Image.new("RGBA", (TILE_SIZE, TILE_SIZE * 2), (0, 0, 0, 0))

    parts = [
        # legs
        (xlegs * TILE_SIZE, (LEGS_Y + ylegs * 2) * TILE_SIZE, TILE_SIZE, TILE_SIZE * 2, leg_color),
        # body
        (body * TILE_SIZE, BODY_Y * TILE_SIZE, TILE_SIZE, TILE_SIZE, body_color),
        # tail
        (tail * TILE_SIZE, TAIL_Y * TILE_SIZE, TILE_SIZE, TILE_SIZE, body_color),
        # mouth
        (mouth * TILE_SIZE, MOUTH_Y * TILE_SIZE, TILE_SIZE, TILE_SIZE, None),
        # eye
        (
            ((EYE_X_BASE + body) if eye_index == 2 else (EYE_X_BASE + eye_index * EYE_X_STRIDE + body)) * TILE_SIZE,
            ((EYE_Y_OFFSET + eye_y) if eye_index == 2 else eye_y) * TILE_SIZE,
            TILE_SIZE, TILE_SIZE, None
        ),
        # antenna
        ((ANTENNA_X + body) * TILE_SIZE, (ANTENNA_Y + antenna) * TILE_SIZE, TILE_SIZE, TILE_SIZE, antenna_color),
    ]

    for x, y, w, h, color in parts:
        paste_tile(canvas, sheet, x, y, w, h, hue_sat=color)

    return canvas

# === 시트 이미지 생성 ===
def generate_creature_sheet(tile_size=16):
    with open(STATIC_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    count = len(lines)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    sheet_img = Image.new("RGBA", (cols * tile_size, rows * tile_size * 2), (0, 0, 0, 0))
    
    size_path = IMAGE_PATH.replace(".png", "_size.jsonl")
    with open(size_path, "w", encoding="utf-8") as size_file:
        for idx, line in enumerate(lines):
            raw = base64.b64decode(line.strip())
            gene = asdict(Genome(raw).traits)
            parts = map_gene_to_parts(gene)
            hs = gene["species_color_rgb"]

            img = generate_creature_image(
                SPRITE_PATH,
                leg_color=(hs[0], hs[1]),
                body_color=(hs[2], hs[3]),
                antenna_color=(hs[4], hs[5]),
                **parts
            )

            x = (idx % cols) * tile_size
            y = (idx // cols) * tile_size * 2
            sheet_img.paste(img, (x, y), img)

            size_file.write(f"{gene['size']:.3f}\n")

            if idx % 100 == 0:
                ratio = idx / count
                percent = ratio * 100
                bar_len = 50
                passed = "=" * int(ratio * bar_len)
                remaining = "-" * (bar_len - len(passed))
                print(f"| {idx}/{count} | {percent:.1f}% {passed}>{remaining}", end='\r')


        sheet_img.save(IMAGE_PATH)
        print(f"✅ 저장 완료: {IMAGE_PATH} ({cols}x{rows})")

from PIL import Image

def load_creatures_from_sheet(indices, tile_size=16):
    """
    생물 시트 이미지에서 여러 개체를 한 번에 불러오고, 좌표와 함께 반환
    :param indices: 불러올 인덱스 리스트 (e.g., [0, 2, 5])
    :param tile_size: 타일 크기 (기본값 16)
    :return: List of (idx, image) tuples, full sheet image
    """
    sheet = Image.open(IMAGE_PATH).convert("RGBA")
    sheet_width, sheet_height = sheet.size
    cols = sheet_width // tile_size

    results = []
    for idx in indices:
        cx = (idx % cols) * tile_size
        cy = (idx // cols) * tile_size * 2  # 높이 2배
        creature = sheet.crop((cx, cy, cx + tile_size, cy + tile_size * 2))
        results.append((idx, creature))

    return results


# === 실행 ===
if __name__ == "__main__":
    generate_creature_sheet()
    creatures = load_creatures_from_sheet([np.random.randint(30000) for _ in range(10000)])
    print(len(creatures))
    # for creature in creatures:
    #     Image._show(creature[1])