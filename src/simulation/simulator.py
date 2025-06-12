from src.core.engine            import World
from src.utils.constants        import *
from src.visualizer.CLI_viewer  import Viewer

import numpy as np
class Simulator:
    def __init__(self, seed=1000005):
        np.random.seed(seed)
        self.world = World()
        self.viewer= Viewer(self.world)

    def run(self):
        while True:
            self.step()

    def step(self):
        self.world.Trun()
        self.viewer.step()