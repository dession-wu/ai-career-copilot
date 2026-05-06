"""
直接测试OCR功能
"""

import sys
sys.path.insert(0, 'e:\\Desktop\\AI Career Co-pilot\\backend')

import os

# 设置EasyOCR模型目录
os.environ['EASYOCR_MODULE_PATH'] = r"D:\AI-Career-Co-pilot\models\easyocr"

# 创建模型目录
model_dir = r"D:\AI-Career-Co-pilot\models\easyocr"
os.makedirs(model_dir, exist_ok=True)

print(f"模型目录: {model_dir}")
print(f"目录存在: {os.path.exists(model_dir)}")
print(f"目录可写: {os.access(model_dir, os.W_OK)}")

# 测试EasyOCR
print("\n正在初始化EasyOCR...")
try:
    import easyocr
    
    reader = easyocr.Reader(
        ['ch_sim', 'en'],
        model_storage_directory=model_dir,
        download_enabled=True,
        verbose=True
    )
    print("✓ EasyOCR初始化成功")
    
    # 测试图片路径（使用原始字符串避免转义问题）
    test_image = r"E:\Desktop\岗位JD.png"
    
    if os.path.exists(test_image):
        print(f"\n正在识别图片: {test_image}")
        # 使用PIL加载图片（支持中文路径），然后转换为numpy数组
        from PIL import Image
        import numpy as np
        pil_image = Image.open(test_image)
        img_array = np.array(pil_image)
        result = reader.readtext(img_array)
        print(f"✓ 识别完成，共 {len(result)} 个文本区域")
        
        print("\n识别结果:")
        for i, detection in enumerate(result[:10]):  # 显示前10个
            text = detection[1]
            confidence = detection[2]
            print(f"  {i+1}. {text} (置信度: {confidence:.2f})")
        
        # 合并所有文本
        all_text = '\n'.join([d[1] for d in result])
        print(f"\n完整文本 ({len(all_text)} 字符):")
        print(all_text[:500] + "..." if len(all_text) > 500 else all_text)
    else:
        print(f"⚠ 测试图片不存在: {test_image}")
        
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
