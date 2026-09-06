import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def resolve_python():
    """选一个装了项目依赖的 Python：优先 3.11（sentence-transformers 3.1.0 要求 numpy<2，仅 3.11 有预编译 wheel）。"""
    candidates = [["py", "-3.11"], ["py", "-3.13"], [sys.executable]]
    for cmd in candidates:
        try:
            subprocess.run(
                cmd + ["-c", "import fastapi, uvicorn, requests"],
                check=True, capture_output=True, timeout=30,
            )
            return cmd
        except Exception:
            continue
    return [sys.executable]


print("启动后端...")
backend = subprocess.Popen(
    resolve_python() + ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    cwd=os.path.join(ROOT, "backend"),
)

print("启动前端...")
frontend = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=os.path.join(ROOT, "frontend"),
    shell=True,
)

print()
print("后端: http://localhost:8000")
print("前端: http://localhost:5173")
print("按 Ctrl+C 关闭")
print()

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    backend.terminate()
    frontend.terminate()
    print("\n已关闭")
