from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.organism import Creature, Corpse


import numpy as np
from src.utils.constants import *
from src.utils.datatypes import Vector2

from typing import List
from collections import defaultdict, deque

def find_closest_point_arg(points: np.array, target: np.array) -> int:
    """주어진 2차원 좌표 배열(points) 중에서 target에 가장 가까운 점의 인덱스를 반환합니다.
    유클리드 거리 제곱 기준으로 계산됩니다.
    """
    dists = np.sum((points - target)**2, axis=1)
    return np.argmin(dists)


def find_closest_point(points: list[Vector2], target: Vector2):
    """주어진 Vector2 리스트 중에서 target에 가장 가까운 점까지의 거리(제곱)와 그 인덱스를 반환합니다."""
    dists = np.sum((points - target)**2, axis=1)
    return np.min(dists), np.argmin(dists)


def get_grid_coords(position: Vector2) -> Vector2:
    """연속 좌표(position)를 그리드 단위 인덱스 좌표로 변환합니다.
    GRID_WIDTH_SCALE 및 GRID_HIGHT_SCALE 기준으로 나눕니다.
    """
    return Vector2(int(position.x // GRID_WIDTH_SCALE), int(position.y // GRID_HIGHT_SCALE))


def apply_weight_or_default(value, weight, default, max_value, min_value=0):
    """값이 존재하면 가중치를 곱하고 최소값(min_value)만큼 더한 뒤,
    max_value를 넘지 않도록 제한하여 반환합니다. 값이 None/0이면 기본값을 반환합니다.
    """
    return min((value * weight)+min_value, max_value) if value else default


def apply_weight_or_default_int(value, weight, default, max_value, min_value=0):
    """apply_weight_or_default의 정수형 버전입니다. 최종 결과를 정수로 반환합니다."""
    return min(int(value * weight)+min_value, max_value) if value else default


def list_apply_weight(values, weight, default, max_value, min_value=0):
    """리스트의 각 값에 apply_weight_or_default를 적용한 값을 리스트로 반환합니다."""
    return [apply_weight_or_default(v, weight, default, max_value, min_value) for v in values]


def list_apply_weight_and_pad(values, weight, default, max_value, target_length, min_value=0):
    """list_apply_weight의 결과를 target_length에 맞게 고정합니다.
    부족한 길이만큼 default 값으로 패딩합니다.
    """
    actual = [apply_weight_or_default(v, weight, default, max_value, min_value) for v in values[:target_length]]
    pad_len = max(0, target_length - len(values))
    return actual + [default] * pad_len


def apply_weights_with_flag(values, weights, max_values, min_values):
    """2차원 리스트 values에 대해 각 행마다 weights를 곱하여 min/max 보정한 값을 반환합니다.
    길이가 weights보다 긴 경우 마지막에 플래그(1)를 붙이고, 짧은 행은 제외합니다.
    """
    w_len = len(weights)
    return [
        [min((v[i] * weights[i])+min_values[i], max_values[i]) for i in range(w_len)] + [int(len(v) > w_len)]
        for v in values if len(v) >= w_len
    ]

def intersect_lists(list1, list2):
    """두 리스트의 공통 요소를 순서 없이 반환"""
    return list(set(list1) & set(list2))

def filter_reachable_loads(start_nodes: List[int], target_nodes: List[int], edges: List[List[int]]) -> List[List[int]]:
    """
    방향성 있는 간선들 중, start_nodes로부터 target_nodes까지 도달 가능한 경로에 포함된 간선만 반환.
    간선은 [u, i, v, j] 형식 (u → v) 으로 주어짐.
    """
    # 1. 방향성 있는 그래프 구성
    graph = defaultdict(list)
    for u, _, v, _ in edges:
        graph[u].append(v)

    # 2. 도달 가능한 노드 집합 계산 (BFS)
    visited = set()
    reachable = set()
    queue = deque(start_nodes)

    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        if node in target_nodes:
            reachable.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                queue.append(neighbor)

    # 3. 간선 필터링: 도달 경로에 있는 간선만 유지 (u → v 형태)
    result = [
        [u, i, v, j]
        for u, i, v, j in edges
        if u in visited and v in visited  # u → v가 방문된 경로 내에 있는 경우
    ]

    return result

def find_creatures_within(creature_self:'Creature', creatures:list['Creature'], max_distance: float) -> list['Creature']:
    """같은 grid 내에서 자신을 제외하고 특정 거리 이하의 모든 개체를 반환"""
    others = [c for c in creatures if c is not creature_self]
    if not others:
        return []

    self_pos = np.array([creature_self.position.x, creature_self.position.y])
    positions = np.array([[c.position.x, c.position.y] for c in others])

    deltas = positions - self_pos
    dists_sq = np.einsum("ij,ij->i", deltas, deltas)
    max_dist_sq = max_distance ** 2

    # 거리 제한 이하인 인덱스 필터링
    valid_indices = np.where(dists_sq <= max_dist_sq)[0]

    return [others[i] for i in valid_indices]

#TODO 특정 공간 안에 가장 가까운 개체.
def find_nearest_creature(creature_self:'Creature', creatures: list['Creature'], max_distance: float):
    """같은 grid 내에서 자신을 제외하고 가장 가까운 개체 하나를 반환"""
    others = [c for c in creatures if c is not creature_self]
    if not others:
        return None

    self_pos = np.array([creature_self.position.x, creature_self.position.y])
    min_dist_sq = max_distance * max_distance
    nearest = None

    for c in others:
        dx = c.position.x - self_pos[0]
        dy = c.position.y - self_pos[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest = c

    return nearest

def find_nearest_corpse(creature_self: 'Creature', corpses: list['Corpse'], max_distance: float):
    """주어진 범위 내에서 가장 가까운 시체를 반환"""
    if not corpses:
        return None

    self_pos = np.array([creature_self.position.x, creature_self.position.y])
    max_dist_sq = max_distance ** 2  # 거리 제곱으로 계산
    min_dist_sq = float('inf')  # 가장 작은 거리의 제곱 값
    nearest = None

    for c in corpses:
        dx = c.position.x - self_pos[0]
        dy = c.position.y - self_pos[1]
        dist_sq = dx * dx + dy * dy

        # 만약 거리가 최대 범위 이하이고, 현재 거리보다 더 작은 거리라면
        if dist_sq < min_dist_sq and dist_sq <= max_dist_sq:
            min_dist_sq = dist_sq
            nearest = c

    return nearest

def find_nearest_object(
    origin_pos: Vector2,
    objects: list,
    max_distance: float,
    exclude_object=None
):
    """
    주어진 위치(origin_pos)에서 max_distance 이내 가장 가까운 개체를 반환
    :param origin_pos: 기준 위치 (x, y)
    :param objects: 거리 비교 대상 객체 리스트
    :param max_distance: 최대 거리
    :param exclude_object: 제외할 객체 (ex: 자기 자신)
    :return: 가장 가까운 객체 또는 None
    """
    max_dist_sq = max_distance ** 2
    min_dist_sq = float('inf')
    nearest = None

    for obj in objects:
        if obj is exclude_object:
            continue
        dx = obj.position.x - origin_pos.x
        dy = obj.position.y - origin_pos.y
        dist_sq = dx * dx + dy * dy

        if dist_sq <= max_dist_sq and dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest = obj

    return nearest


def gene_similarity(a: str, b: str, length: int = 100) -> float:
    """두 유전자 문자열 간 유사도 (0.0 ~ 1.0)"""
    max_len = min(len(a), len(b), length)
    if max_len == 0:
        return 0.0
    same = sum(1 for i in range(max_len) if a[i] == b[i])
    return same / max_len