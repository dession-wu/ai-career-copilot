"""
预下载EasyOCR模型文件到项目目录
"""

import os
import urllib.request
import zipfile

# 设置模型目录 - 使用项目目录
model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'models', 'easyocr', 'model')
os.makedirs(model_dir, exist_ok=True)

print(f"模型目录: {model_dir}")

# EasyOCR需要的模型文件
models = {
    "craft_mlt_25k.pth": {
        "url": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip",
        "filename": "craft_mlt_25k.zip"
    },
    "latin.pth": {
        "url": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/latin.zip",
        "filename": "latin.zip"
    },
    "chinese_sim.pth": {
        "url": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/chinese_sim.zip",
        "filename": "chinese_sim.zip"
    }
}

print("=" * 60)
print("下载EasyOCR模型文件")
print("=" * 60)

for model_name, model_info in models.items():
    model_path = os.path.join(model_dir, model_name)
    
    if os.path.exists(model_path):
        print(f"✓ {model_name} 已存在")
        continue
    
    zip_path = os.path.join(model_dir, model_info["filename"])
    
    print(f"\n下载 {model_info['filename']}...")
    try:
        urllib.request.urlretrieve(model_info["url"], zip_path)
        print(f"✓ 下载完成: {zip_path}")
        
        # 解压
        print(f"解压 {model_info['filename']}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        print(f"✓ 解压完成")
        
        # 删除zip文件
        os.remove(zip_path)
        print(f"✓ 清理完成")
        
    except Exception as e:
        print(f"✗ 下载失败: {e}")

print("\n" + "=" * 60)
print("模型文件列表:")
for f in os.listdir(model_dir):
    file_path = os.path.join(model_dir, f)
    size = os.path.getsize(file_path)
    print(f"  {f} ({size / 1024 / 1024:.1f} MB)")
print("=" * 60)
