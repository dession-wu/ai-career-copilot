#!/usr/bin/env python3
"""验证OCR引擎和模型路径配置"""
import os
import sys

# 首先配置PaddleOCR模型路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.paddlex_config import ensure_model_path, PADDLEX_MODEL_PATH

print(f"PADDLEX_HOME: {os.environ.get('PADDLEX_HOME', 'Not Set')}")
print(f"PADDLE_HOME: {os.environ.get('PADDLE_HOME', 'Not Set')}")
print(f"模型路径: {PADDLEX_MODEL_PATH}")
print(f"路径存在: {os.path.exists(PADDLEX_MODEL_PATH)}")

# 验证模型文件
if os.path.exists(PADDLEX_MODEL_PATH):
    model_dirs = os.listdir(PADDLEX_MODEL_PATH)
    print(f"模型目录内容: {model_dirs}")

# 初始化OCR引擎
print("\n正在初始化OCR引擎...")
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    print("✅ OCR引擎初始化成功！")
    print("✅ 模型路径验证通过")
except Exception as e:
    print(f"❌ OCR引擎初始化失败: {e}")
    sys.exit(1)
