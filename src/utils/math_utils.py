import numpy as np
import src.utils.datatypes as datatype

def find_closest_point_arg(points: np.array, target: np.array) -> int:
	"""타겟 위치에서 가장 가까운 요소 반환"""
	dists = np.sum((points - target)**2, axis=1)
	return np.argmin(dists)

def find_closest_point(points: list[datatype.Vector2], target: datatype.Vector2):
	"""타겟 위치에서 가장 가까운 위치와 요소 반환"""
	dists = np.sum((points - target)**2, axis=1)
	return np.min(dists), np.argmin(dists)


def apply_weight_or_default(value, weight, default, max_value, min_value=0):
    """값이 존재하면 가중치를 곱하고, 없으면 기본값 반환"""
    return min((value * weight)+min_value, max_value) if value else default

def apply_weight_or_default_int(value, weight, default, max_value, min_value=0):
    """값이 존재하면 가중치를 곱하고, 없으면 기본값 반환"""
    return min(int(value * weight)+min_value, max_value) if value else default

def list_apply_weight(values, weight, default, max_value, min_value=0):
    """정수 리스트에 가중치 적용"""
    return [apply_weight_or_default(v, weight, default, max_value, min_value) for v in values]

def list_apply_weight_and_pad(values, weight, default, max_value, target_length, min_value=0):
    """정수 리스트에 가중치 적용 후 길이를 고정하고 부족분을 기본값으로 패딩"""
    actual = [apply_weight_or_default(v, weight, default, max_value, min_value) for v in values[:target_length]]
    pad_len = max(0, target_length - len(values))
    return actual + [default] * pad_len

def apply_weights_with_flag(values, weights, max_values, min_values):
    """가중치 적용 + 플래그, 길이 짧은 row는 제외"""
    w_len = len(weights)
    return [
        [min((v[i] * weights[i])+min_values[i], max_values[i]) for i in range(w_len)] + [int(len(v) > w_len)]
        for v in values if len(v) >= w_len
    ]
