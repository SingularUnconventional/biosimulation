import os
import signal
import subprocess
from pathlib import Path

import sys
import os

# 현재 파일 기준으로 상위 폴더 경로 계산
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

PID_FILE = Path("pid.txt")
LOG_FILE = Path("logs/simulation.log")

def is_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def start_server():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        if is_running(pid):
            print(f"[✓] 서버가 이미 실행 중입니다. (PID: {pid})")
            return

    proc = subprocess.Popen(
        ["python3", "main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PID_FILE.write_text(str(proc.pid))
    print(f"[✓] 서버 시작됨 (PID: {proc.pid})")

def stop_server():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[✓] 서버 종료됨 (PID: {pid})")
        except ProcessLookupError:
            print("[!] 실행 중인 서버 프로세스가 없습니다.")
        PID_FILE.unlink()
    else:
        print("[!] 서버가 실행 중이지 않습니다.")

def server_status():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        if is_running(pid):
            print(f"[✓] 서버 실행 중 (PID: {pid})")
            return
    print("[✗] 서버가 중지됨")

def show_log(n=10):
    if not LOG_FILE.exists():
        print("[!] 로그 없음")
        return
    with LOG_FILE.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-n:]
        print("─ 최근 로그 ─")
        for line in lines:
            print(line.rstrip())

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start_server()
    elif cmd == "stop":
        stop_server()
    elif cmd == "status":
        server_status()
    elif cmd == "log":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        show_log(n)
    else:
        print("명령어: start | stop | status | log [N]")