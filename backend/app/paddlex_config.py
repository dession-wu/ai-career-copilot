"""
PaddleOCR 模型路径配置
支持跨平台：默认使用项目根目录下 models/paddlex，可通过环境变量 PADDLEX_MODEL_DIR 覆盖
"""
import os
from pathlib import Path

# 模型根目录：项目根目录（backend 的上一级）下的 models/
# 可通过环境变量 PADDLEX_MODEL_DIR 指定绝对路径覆盖
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PADDLEX_MODEL_PATH = os.environ.get("PADDLEX_MODEL_DIR") or str(
    _PROJECT_ROOT / "models" / "paddlex"
)

# 设置环境变量
os.environ["PADDLEX_HOME"] = PADDLEX_MODEL_PATH
os.environ["PADDLE_HOME"] = PADDLEX_MODEL_PATH

# 禁用OneDNN加速，解决CPU兼容性问题
os.environ['FLAGS_use_mkldnn'] = 'False'
os.environ['FLAGS_cpu_deterministic'] = 'True'
os.environ['CPU_NUM'] = '1'

# 禁用PaddlePaddle的某些优化，提高兼容性
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'
os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0'

def ensure_model_path():
    """确保模型路径存在"""
    if not os.path.exists(PADDLEX_MODEL_PATH):
        try:
            os.makedirs(PADDLEX_MODEL_PATH, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f"无法创建 PaddleOCR 模型目录 {PADDLEX_MODEL_PATH}：{e}。"
                f"请检查目录权限，或通过环境变量 PADDLEX_MODEL_DIR 指定一个可写的目录"
            ) from e
        print(f"[PaddleX] 创建模型目录: {PADDLEX_MODEL_PATH}")
    else:
        print(f"[PaddleX] 使用模型目录: {PADDLEX_MODEL_PATH}")

# 在导入时执行
ensure_model_path()
