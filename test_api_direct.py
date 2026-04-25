"""
直接测试后端API
"""

import requests
import os

# API配置
API_URL = "http://localhost:8000/api/jobs/extract"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXNzaW9uIiwiZXhwIjoxNzc2ODYwMzQyfQ.8e3dTenNIljUFq0_tHF4gcXA0Qlcy7EdpH6FdmNU16g"

# 测试图片路径
image_path = r"E:\Desktop\岗位JD.png"

print("=" * 60)
print("直接测试后端API")
print("=" * 60)

# 检查文件是否存在
if not os.path.exists(image_path):
    print(f"✗ 图片不存在: {image_path}")
    exit(1)

print(f"✓ 图片存在: {image_path}")
print(f"  文件大小: {os.path.getsize(image_path)} bytes")

# 准备请求
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 准备文件
with open(image_path, "rb") as f:
    files = {
        "file": ("岗位JD.png", f, "image/png")
    }
    
    print(f"\n发送POST请求到: {API_URL}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.post(API_URL, headers=headers, files=files, timeout=60)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容:")
        print(response.text)
        
        if response.status_code == 200:
            print("\n✅ API调用成功")
            data = response.json()
            print(f"消息: {data.get('message', 'N/A')}")
            print(f"数据: {data.get('data', 'N/A')}")
        else:
            print(f"\n✗ API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
