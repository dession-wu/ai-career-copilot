"""
PaddleOCR 模型路径配置
将模型文件从C盘移动到D盘，减少C盘空间占用
"""
import os

# 设置PaddleOCR模型路径为D盘
PADDLEX_MODEL_PATH = r"D:\AI-Career-Co-pilot\models\paddlex"

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
        os.makedirs(PADDLEX_MODEL_PATH, exist_ok=True)
        print(f"[PaddleX] 创建模型目录: {PADDLEX_MODEL_PATH}")
    else:
        print(f"[PaddleX] 使用模型目录: {PADDLEX_MODEL_PATH}")

# 在导入时执行
ensure_model_path()
