"""
直接测试ImageOCRParser
"""

import sys
sys.path.insert(0, 'e:\\Desktop\\AI Career Co-pilot\\backend')

import os

# 设置环境变量
os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['EASYOCR_MODULE_PATH'] = r"D:\AI-Career-Co-pilot\models\easyocr"

# 创建模型目录
model_dir = r"D:\AI-Career-Co-pilot\models\easyocr"
os.makedirs(model_dir, exist_ok=True)

print("=" * 60)
print("直接测试ImageOCRParser")
print("=" * 60)

# 导入parser
from app.services.job_extraction.parsers import ImageOCRParser

# 创建parser实例
parser = ImageOCRParser()

# 测试图片路径
image_path = r"E:\Desktop\岗位JD.png"

print(f"\n测试图片: {image_path}")
print(f"文件存在: {os.path.exists(image_path)}")

if os.path.exists(image_path):
    print("\n开始解析...")
    try:
        success, text, error = parser.parse(image_path)
        
        print(f"\n解析结果:")
        print(f"  成功: {success}")
        print(f"  错误: {error}")
        print(f"  文本长度: {len(text) if text else 0}")
        print(f"  文本预览: {text[:200]}..." if text and len(text) > 200 else f"  文本: {text}")
        
        if success and text:
            print("\n✅ OCR解析成功")
        else:
            print(f"\n✗ OCR解析失败: {error}")
            
    except Exception as e:
        print(f"\n✗ 解析过程出错: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ 图片文件不存在")
