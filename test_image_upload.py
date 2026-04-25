"""
图片上传功能测试脚本
用于测试OCR图片上传和提取功能
"""

import asyncio
import sys
from playwright.async_api import async_playwright

# 测试用的有效JWT token（使用数据库中存在的用户"dession"）
# 使用后端相同的SECRET_KEY生成
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXNzaW9uIiwiZXhwIjoxNzc2ODYwMzQyfQ.8e3dTenNIljUFq0_tHF4gcXA0Qlcy7EdpH6FdmNU16g"

async def test_image_upload():
    """测试图片上传功能"""
    print("=" * 60)
    print("开始测试图片上传功能")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
        # 启用控制台日志捕获
        page = await context.new_page()
        
        console_logs = []
        network_logs = []
        
        def handle_console(msg):
            log_entry = f"[{msg.type}] {msg.text}"
            console_logs.append(log_entry)
            print(f"[Console] {log_entry}")
        
        def handle_request(request):
            network_logs.append(f"[Request] {request.method} {request.url}")
        
        def handle_response(response):
            status = response.status
            url = response.url
            network_logs.append(f"[Response] {status} {url}")
            print(f"[Network] {status} {url}")
        
        page.on("console", handle_console)
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        try:
            # 1. 先访问首页并设置token
            print("\n[步骤1] 访问首页并设置认证token...")
            await page.goto("http://localhost:3000/zh")
            await page.wait_for_load_state("networkidle")
            
            # 在localStorage中设置token和user（模拟已登录）
            # 注意：zustand persist使用特定的存储键名
            await page.evaluate(f"""
                // 设置zustand persist存储
                const storeData = {{
                    state: {{
                        user: {{id: 'test-user-id', username: 'test', email: 'test@example.com'}},
                        token: '{TEST_TOKEN}'
                    }},
                    version: 0
                }};
                localStorage.setItem('app-storage', JSON.stringify(storeData));
                
                // 同时设置单独的token和user供其他组件使用
                localStorage.setItem('token', '{TEST_TOKEN}');
                localStorage.setItem('user', JSON.stringify({{id: 'test-user-id', username: 'test', email: 'test@example.com'}}));
            """)
            print("✓ 已设置认证信息到localStorage")
            
            await asyncio.sleep(1)
            
            # 2. 导航到岗位JD提取页面
            print("\n[步骤2] 导航到岗位JD提取页面...")
            await page.goto("http://localhost:3000/zh/jobs/extract")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            await page.screenshot(path="e:\\Desktop\\AI Career Co-pilot\\test_screenshots\\step1_extract_page.png")
            print("✓ 已进入岗位JD提取页面")
            
            # 3. 查找文件上传区域
            print("\n[步骤3] 查找文件上传控件...")
            
            # 等待页面完全渲染
            await asyncio.sleep(2)
            
            # 查找文件输入框（react-dropzone创建的隐藏input）
            file_input = None
            try:
                # 尝试多种方式找到文件输入
                file_input = await page.wait_for_selector('input[type="file"]', timeout=5000)
                print("✓ 找到文件上传输入框")
            except Exception as e:
                print(f"⚠ 未找到文件输入，尝试通过点击上传区域触发...")
                # 点击上传区域
                upload_area = await page.wait_for_selector('div.border-dashed, div.cursor-pointer', timeout=5000)
                if upload_area:
                    await upload_area.click()
                    await asyncio.sleep(1)
                    file_input = await page.wait_for_selector('input[type="file"]', timeout=5000)
            
            if not file_input:
                raise Exception("无法找到文件上传输入框")
            
            # 4. 上传测试图片
            print("\n[步骤4] 上传测试图片...")
            test_image_path = "E:\\Desktop\\岗位JD.png"
            
            # 检查文件是否存在
            import os
            if not os.path.exists(test_image_path):
                print(f"⚠ 测试图片不存在: {test_image_path}")
                print("  请确认文件路径正确")
                # 尝试使用其他路径
                alt_paths = [
                    "E:\\Desktop\\AI Career Co-pilot\\test_image.png",
                    "E:\\Desktop\\test.png",
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        test_image_path = alt_path
                        print(f"  使用替代图片: {test_image_path}")
                        break
                else:
                    # 创建一个简单的测试图片
                    print("  创建测试图片...")
                    from PIL import Image, ImageDraw, ImageFont
                    img = Image.new('RGB', (800, 600), color='white')
                    draw = ImageDraw.Draw(img)
                    draw.text((50, 50), "测试岗位JD", fill='black')
                    draw.text((50, 100), "职位: 软件工程师", fill='black')
                    draw.text((50, 150), "公司: 测试公司", fill='black')
                    draw.text((50, 200), "要求: 3年以上经验", fill='black')
                    test_image_path = "e:\\Desktop\\AI Career Co-pilot\\test_image.png"
                    img.save(test_image_path)
                    print(f"  已创建测试图片: {test_image_path}")
            
            await file_input.set_input_files(test_image_path)
            print(f"✓ 已选择文件: {test_image_path}")
            
            await asyncio.sleep(2)
            await page.screenshot(path="e:\\Desktop\\AI Career Co-pilot\\test_screenshots\\step2_file_selected.png")
            
            # 5. 查找并点击"开始提取"按钮
            print("\n[步骤5] 点击开始提取按钮...")
            
            # 查找开始提取按钮
            extract_button = await page.wait_for_selector('button:has-text("开始提取")', timeout=5000)
            await extract_button.click()
            print("✓ 已点击开始提取按钮")
            
            # 6. 等待OCR处理结果
            print("\n[步骤6] 等待OCR处理结果...")
            print("  等待20秒让OCR处理完成...")
            await asyncio.sleep(20)
            
            await page.screenshot(path="e:\\Desktop\\AI Career Co-pilot\\test_screenshots\\step3_result.png")
            
            # 7. 检查提取结果
            print("\n[步骤7] 检查提取结果...")
            
            # 获取页面内容检查是否有结果
            page_content = await page.content()
            page_text = await page.evaluate("() => document.body.innerText")
            
            # 查找成功标志
            success_indicators = ['提取成功', '职位信息', '确认', '核对', '智能提取']
            found_success = any(indicator in page_content for indicator in success_indicators)
            
            if found_success:
                print("✓ 页面显示提取成功相关信息")
            
            # 检查是否有错误信息
            error_indicators = ['错误', '失败', 'Error', 'Failed', '401', '500']
            found_error = any(err in page_content for err in error_indicators)
            
            if found_error:
                print("⚠ 页面可能包含错误信息")
            
            # 8. 输出日志总结
            print("\n" + "=" * 60)
            print("测试完成 - 日志总结")
            print("=" * 60)
            
            print(f"\n[控制台日志] 共 {len(console_logs)} 条")
            for log in console_logs[-20:]:  # 显示最后20条
                print(f"  {log}")
            
            print(f"\n[网络请求] 共 {len(network_logs)} 条")
            # 只显示与API相关的请求
            api_requests = [log for log in network_logs if '/api/' in log]
            for log in api_requests[-10:]:
                print(f"  {log}")
            
            # 检查是否有错误
            errors = [log for log in console_logs if "error" in log.lower() or "Error" in log]
            if errors:
                print(f"\n⚠ 发现 {len(errors)} 条错误日志:")
                for err in errors[:10]:
                    print(f"  {err}")
            else:
                print("\n✓ 未发现错误日志")
            
            # 检查网络请求状态
            failed_requests = [log for log in network_logs if log.startswith("[Response]") and any(str(code) in log for code in [401, 403, 404, 500, 502, 503])]
            if failed_requests:
                print(f"\n⚠ 发现失败的网络请求:")
                for req in failed_requests[:10]:
                    print(f"  {req}")
            else:
                print("✓ 所有网络请求正常（无401/403/404/500错误）")
            
            # 最终结论
            print("\n" + "=" * 60)
            if not errors and not failed_requests:
                print("✅ 测试通过：图片上传功能正常工作")
            elif not failed_requests:
                print("⚠️  测试部分通过：无网络错误，但可能有其他问题")
            else:
                print("❌ 测试失败：发现网络错误或服务器错误")
                print("\n需要修复的问题:")
                for req in failed_requests[:5]:
                    print(f"  - {req}")
            print("=" * 60)
            
            print(f"\n截图已保存到: e:\\Desktop\\AI Career Co-pilot\\test_screenshots\\")
            
        except Exception as e:
            print(f"\n✗ 测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 错误时截图
            try:
                await page.screenshot(path="e:\\Desktop\\AI Career Co-pilot\\test_screenshots\\error_screenshot.png")
                print("✓ 错误截图已保存")
            except:
                pass
                
        finally:
            await asyncio.sleep(3)
            await browser.close()

if __name__ == "__main__":
    # 创建截图目录
    import os
    os.makedirs("e:\\Desktop\\AI Career Co-pilot\\test_screenshots", exist_ok=True)
    
    asyncio.run(test_image_upload())
