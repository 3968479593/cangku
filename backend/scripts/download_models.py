import sys
import os

# ---- 设置 HuggingFace 镜像（国内用户必需） ----
# 可通过环境变量覆盖: set HF_ENDPOINT=https://hf-mirror.com
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from huggingface_hub import snapshot_download

models = [
    "BAAI/bge-m3",
    "BAAI/bge-reranker-v2-m3",
]

# 模型缓存到 backend/models 目录
cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
os.makedirs(cache_dir, exist_ok=True)

print(f"镜像地址: {os.environ['HF_ENDPOINT']}")
print(f"缓存目录: {cache_dir}")

for model_name in models:
    print(f"\n{'='*50}")
    print(f"正在下载: {model_name}")
    print(f"{'='*50}")
    try:
        path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            resume_download=True,
        )
        print(f"\n完成! 存储路径: {path}")
    except Exception as e:
        print(f"\n下载失败: {e}")
        print("提示：如果下载失败，可以尝试其他镜像：")
        print("  set HF_ENDPOINT=https://hf.xeduapi.com")
        print("  或从 ModelScope 手动下载: https://modelscope.cn/models/BAAI/bge-m3")
        continue

print("\n全部模型下载完成!")
