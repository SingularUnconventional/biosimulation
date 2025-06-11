import numpy as np
from src.utils.constants import THRESHOLD_WEIGHT

class _ActivationFunctions:
    @staticmethod
    def step(x):
        return np.where(x >= 1, 1, 0)

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    @staticmethod
    def tanh(x):
        return np.tanh(x)

    @staticmethod
    def relu(x):
        return np.maximum(0, x)

    @staticmethod
    def leaky_relu(x, alpha=0.01):
        return np.where(x > 0, x, alpha * x)

    @staticmethod
    def elu(x, alpha=1.0):
        return np.where(x >= 0, x, alpha * (np.exp(x) - 1))

    @staticmethod
    def softmax(x):
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)

def brain_calculation(nodes : np.ndarray, synapses : list[list]):
    result = nodes.copy()
    for cns in synapses:
        if result[int(cns[0])][1]:
            if cns[3]: result[int(cns[2]), 2] += result[int(cns[0]), 1]*cns[1]*THRESHOLD_WEIGHT
            else:      result[int(cns[2]), 0] += result[int(cns[0]), 1]*cns[1]

    result[:, 1] = _ActivationFunctions.sigmoid(result[:, 0]+result[:, 2])
    result[:, 0] = 0

    return result
# TODO 역치 한계값 조정 필요 -> 오버플로우 발생. 대안 1. 가중값에 역치를 나눠 역치가 커질수록 가중값이 작아지도록 설정.
if __name__ == '__main__':
    import time

    cycle = 1

    synapses = [
        [0, 1.0, 1, 0],
        [0,-0.5, 2, 0],
        [0,-0.5, 4, 0],
        [0,-0.5, 6, 0],
        [1, 1.0, 1, 0],
        [1, 1.0, 2, 0],
        [1, 1.5, 6, 0],
        [2, 1.0, 3, 0],
        [3, 1.0, 3, 0],
        [3,-0.5, 6, 0],
        [4,-0.5, 1, 0],
        [4,-0.5, 3, 0],
        [4,-0.5, 5, 0],
        [5, 1.0, 4, 0],
        [5, 1.0, 5, 0],
        [6,-0.5, 4, 0],
        [6, 1.0, 5, 0],
    ]

    arr = np.array(synapses)
    brain_max_nodeInx = int(np.max(arr[:, :2]))

    brain_nodes    : np.ndarray = np.zeros((brain_max_nodeInx+1, 3))

    while True:
        input_nodes = input().split()
        try:
            int(input_nodes[0])
        except:
            break
        
        startTime = time.time()

        for _ in range(cycle):
            for i, node in enumerate(input_nodes):
                brain_nodes[i][1] = int(node)
            brain_nodes = brain_calculation(brain_nodes, synapses)


        endTime = time.time() - startTime
        
        for node in brain_nodes:
            print(node[1], end=' ')
        print('\ntime :', endTime)
