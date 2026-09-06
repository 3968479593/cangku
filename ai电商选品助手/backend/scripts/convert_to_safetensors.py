"""把 bge-m3 的 pytorch_model.bin 本地转换为 model.safetensors。

背景：transformers 4.57 因 CVE-2025-32434 禁止 torch<2.6 使用 torch.load 加载
.bin/.pt 权重，但明确说明 safetensors 格式不受此限制。bge-m3 仓库未提供
safetensors 文件，故本地转换一份，让 from_pretrained 自动优先使用。

同时转换 colbert_linear.pt / sparse_linear.pt，避免 FlagEmbedding 加载稀疏/
colbert 头时再次触发 torch.load 限制。
"""
import os
import torch
from safetensors.torch import save_file

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "BAAI", "bge-m3"
)


def _resolve_shared_tensors(state_dict: dict) -> dict:
    """safetensors 不允许共享同一块内存的张量；克隆后即可写入。"""
    seen_ptrs: dict[int, str] = {}
    for k, v in state_dict.items():
        if not torch.is_tensor(v) or not v.is_floating_point():
            continue
        ptr = v.data_ptr()
        if ptr in seen_ptrs:
            state_dict[k] = v.clone()
        else:
            seen_ptrs[ptr] = k
    return state_dict


def convert(src_name: str, dst_name: str):
    src = os.path.join(MODEL_DIR, src_name)
    dst = os.path.join(MODEL_DIR, dst_name)
    if not os.path.exists(src):
        print(f"跳过（不存在）: {src_name}")
        return
    if os.path.exists(dst):
        print(f"跳过（已存在）: {dst_name}")
        return

    print(f"转换 {src_name} -> {dst_name} ...")
    # torch 2.5.1 默认 weights_only=False；本地可信文件直接加载
    state_dict = torch.load(src, map_location="cpu", weights_only=False)
    state_dict = _resolve_shared_tensors(state_dict)
    save_file(state_dict, dst, metadata={"format": "pt"})
    size_mb = os.path.getsize(dst) / 1024 / 1024
    print(f"  完成，大小 {size_mb:.1f} MB")


if __name__ == "__main__":
    print(f"模型目录: {MODEL_DIR}\n")
    convert("pytorch_model.bin", "model.safetensors")
    convert("colbert_linear.pt", "colbert_linear.safetensors")
    convert("sparse_linear.pt", "sparse_linear.safetensors")
    print("\n全部转换完成。重启后端即可生效。")
