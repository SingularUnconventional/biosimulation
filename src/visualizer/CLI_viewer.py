from src.core.engine        import World
from src.entities.organism import Creature
from src.utils.constants    import *

import threading
import time
import sys
from time import time, strftime, localtime
#from colorama import Fore, Style

import os
import logging

# 로그 디렉토리 및 설정
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/simulation.log",
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

class Viewer:
    def __init__(self, world: World):
        self.world = world
        self.count = 0
        self.start_time = time()
        self.creature_count = 0
        self.running = True
        self.paused = False
        self.command = ""
        self.last_rendered_lines = 0

        threading.Thread(target=self.read_input, daemon=True).start()

    def read_input(self):
        while self.running:
            try:
                self.command = input().strip().lower()
                if self.command == "s":
                    self.paused = False
                elif self.command == "p":
                    self.paused = True
                elif self.command == "e":
                    self.running = False
                else:
                    print("알 수 없는 명령어입니다.")
            except EOFError:
                continue


    def step(self):
        self.count += 1

        if self.count % 100 == 0:
            # 유니크 개체 수 계산
            creature_set = set()
            for y in range(WORLD_HIGHT_SCALE):
                for x in range(WORLD_WIDTH_SCALE):
                    creature_set.update(self.world.world[y][x].creatures)
            self.creature_count = len(creature_set)

            # 시간 및 속도 계산
            now = time()
            elapsed = now - self.start_time
            speed = self.count / elapsed if elapsed > 0 else 0
            now_str = strftime("%Y-%m-%d %H:%M:%S", localtime(now))

            # 로그 파일 기록
            logger.info(
                f"[{now_str}]  "
                f"Step: {self.count:6d}  |  "
                f"Unique: {self.creature_count:4d}  |  "
                f"Speed: {speed:7.2f} steps/sec  |  "
                f"Elapsed: {elapsed:6.1f}s"
            )

    def __step(self):
        if not self.running:
            exit()
        if self.paused:
            return

        self.count += 1

        # 100턴마다 개체 수 갱신
        if self.count % 100 == 0:
            creature_set = set()
            for y in range(WORLD_HIGHT_SCALE):
                for x in range(WORLD_WIDTH_SCALE):
                    creature_set.update(self.world.world[y][x].creatures)
            self.creature_count = len(creature_set)

        # 정보 계산
        elapsed = time() - self.start_time
        speed = self.count / elapsed if elapsed > 0 else 0

        # 이전 출력 제거
        if self.last_rendered_lines:
            print("\033[F" * (self.last_rendered_lines+1), end="")

        # 정보 출력
        lines = [
            f"{Fore.LIGHTBLACK_EX}┌─ Simulation Status──────────────────────────────────────────────────────────────────{Style.RESET_ALL}",
            f"│ Step: {Fore.LIGHTWHITE_EX}{self.count:5}{Style.RESET_ALL}  "
            f"Unique Creatures: {Fore.CYAN}{self.creature_count:5}{Style.RESET_ALL}  "
            f"Speed: {Fore.YELLOW}{speed:6.2f} steps/sec{Style.RESET_ALL}  "
            f"Elapsed: {Fore.GREEN}{elapsed:6.1f}s{Style.RESET_ALL}    ",
            f"{Fore.LIGHTBLACK_EX}└─────────────────────────────────────────────────────────────────────────────────────{Style.RESET_ALL}"
        ]
        for line in lines:
            print(line)

        print(f" command - s(start) / p(pause) / e:(exit)", flush=True)

        self.last_rendered_lines = len(lines)
