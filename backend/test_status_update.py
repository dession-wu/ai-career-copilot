"""
测试状态更新功能
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_status_update():
    """测试状态更新API"""
    print("=" * 60)
    print("开始测试状态更新功能")
    print("=" * 60)

    # 1. 测试登录获取token
    print("\n[测试1] 用户登录...")
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✓ 登录成功，获取到访问令牌")
        else:
            print(f"✗ 登录失败: {response.status_code}")
            print(f"  响应: {response.text}")
            # 如果没有测试用户，跳过此测试
            print("  跳过需要认证的测试")
            access_token = None
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")
        access_token = None

    if not access_token:
        print("\n[!] 无法获取访问令牌，跳过后续测试")
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. 获取职位列表
    print("\n[测试2] 获取职位列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
        if response.status_code == 200:
            jobs = response.json()
            print(f"✓ 成功获取职位列表，共 {len(jobs)} 条记录")

            if jobs:
                test_job = jobs[0]
                job_id = test_job["id"]
                current_status = test_job["status"]
                print(f"  选择测试职位: {test_job['job_title']} @ {test_job['company_name']}")
                print(f"  当前状态: {current_status}")
            else:
                print("  职位列表为空，跳过状态更新测试")
                return
        else:
            print(f"✗ 获取职位列表失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return
    except Exception as e:
        print(f"✗ 获取职位列表失败: {e}")
        return

    # 3. 测试正常状态更新
    print("\n[测试3] 正常状态更新...")
    status_update_data = {
        "new_status": "interviewing",
        "changed_at": datetime.utcnow().isoformat(),
        "notes": "测试状态更新",
        "metadata": {
            "interview_date": datetime.utcnow().isoformat(),
            "interview_type": "video",
            "interview_round": 1
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/{job_id}/status-with-history",
            json=status_update_data,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 状态更新成功")
            print(f"  旧状态: {result.get('old_status')}")
            print(f"  新状态: {result.get('new_status')}")
            print(f"  变更时间: {result.get('changed_at')}")
        else:
            print(f"✗ 状态更新失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 状态更新请求失败: {e}")

    # 4. 测试无效状态值
    print("\n[测试4] 无效状态值测试...")
    invalid_status_data = {
        "new_status": "invalid_status",
        "changed_at": datetime.utcnow().isoformat()
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/{job_id}/status-with-history",
            json=invalid_status_data,
            headers=headers
        )

        if response.status_code == 400:
            print(f"✓ 无效状态值被正确拒绝 (400)")
            print(f"  错误信息: {response.json().get('detail', '未知错误')}")
        else:
            print(f"✗ 预期返回400，实际返回: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 无效状态值测试失败: {e}")

    # 5. 测试不存在的职位ID
    print("\n[测试5] 不存在的职位ID测试...")
    fake_job_id = "00000000-0000-0000-0000-000000000000"

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/{fake_job_id}/status-with-history",
            json=status_update_data,
            headers=headers
        )

        if response.status_code == 404:
            print(f"✓ 不存在的职位ID被正确拒绝 (404)")
            print(f"  错误信息: {response.json().get('detail', '未知错误')}")
        else:
            print(f"✗ 预期返回404，实际返回: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 不存在的职位ID测试失败: {e}")

    # 6. 测试状态历史查询
    print("\n[测试6] 状态历史查询...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}/status-history",
            headers=headers
        )

        if response.status_code == 200:
            history_data = response.json()
            history = history_data.get("history", [])
            total = history_data.get("total", 0)
            print(f"✓ 成功获取状态历史，共 {total} 条记录")

            for i, record in enumerate(history[:3], 1):  # 只显示前3条
                print(f"  记录{i}: {record.get('old_status')} -> {record.get('new_status')} @ {record.get('changed_at')}")
        else:
            print(f"✗ 获取状态历史失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 状态历史查询失败: {e}")

    # 7. 恢复原始状态
    print("\n[测试7] 恢复原始状态...")
    restore_data = {
        "new_status": current_status,
        "changed_at": datetime.utcnow().isoformat(),
        "notes": "测试完成后恢复原状态"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/{job_id}/status-with-history",
            json=restore_data,
            headers=headers
        )

        if response.status_code == 200:
            print(f"✓ 成功恢复到原始状态: {current_status}")
        else:
            print(f"✗ 恢复状态失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 恢复状态请求失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_status_update()
