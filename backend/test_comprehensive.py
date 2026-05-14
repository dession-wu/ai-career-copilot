"""
全面功能测试脚本
测试范围：API路由、数据库模型、Agent核心、记忆系统
"""

import sys
sys.path.insert(0, "e:\\Desktop\\AI Career Co-pilot\\backend")

def test_api_routes():
    """测试API路由加载"""
    print("=== API路由测试 ===")
    from app.main import app
    from fastapi.routing import APIRoute
    
    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    print(f"总路由数: {len(routes)}")
    
    # 检查关键路由存在
    paths = [r.path for r in routes]
    key_routes = [
        "/api/agents/tailor-resume",
        "/api/agents/tailor-resume/workflow",
        "/api/agents/memory/preference",
        "/api/agents/health",
        "/api/auth/login",
        "/api/vault",
        "/api/jobs",
    ]
    
    for route in key_routes:
        status = "OK" if route in paths else "MISSING"
        print(f"  {route}: {status}")
    
    return len(routes)

def test_database_models():
    """测试数据库模型"""
    print("\n=== 数据库模型测试 ===")
    from app.database import Base, engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"数据库表数量: {len(tables)}")
    
    # 检查核心表
    core_tables = [
        "users", "career_vaults", "job_applications",
        "interview_questions", "interview_reviews"
    ]
    for t in core_tables:
        status = "OK" if t in tables else "MISSING"
        print(f"  {t}: {status}")
    
    return len(tables)

def test_agent_tools():
    """测试Agent工具"""
    print("\n=== Agent工具测试 ===")
    
    tools_tested = 0
    
    try:
        from app.tools.vault_tools_v2 import search_vault_v2
        print("  vault_tools_v2: OK")
        tools_tested += 1
    except Exception as e:
        print(f"  vault_tools_v2: FAIL - {e}")
    
    try:
        from app.tools.job_tools_v2 import calculate_match_score_parallel
        print("  job_tools_v2: OK")
        tools_tested += 1
    except Exception as e:
        print(f"  job_tools_v2: FAIL - {e}")
    
    try:
        from app.tools.verification_tools import verify_facts
        print("  verification_tools: OK")
        tools_tested += 1
    except Exception as e:
        print(f"  verification_tools: FAIL - {e}")
    
    try:
        from app.tools.resume_tools import generate_resume_section
        print("  resume_tools: OK")
        tools_tested += 1
    except Exception as e:
        print(f"  resume_tools: FAIL - {e}")
    
    return tools_tested

def test_workflow():
    """测试工作流"""
    print("\n=== 工作流测试 ===")
    
    try:
        from app.graphs.resume_workflow import create_resume_workflow
        workflow = create_resume_workflow()
        has_invoke = hasattr(workflow, "invoke")
        print(f"  resume_workflow: OK (invoke={has_invoke})")
        return 1
    except Exception as e:
        print(f"  resume_workflow: FAIL - {e}")
        return 0

def test_memory_system():
    """测试记忆系统"""
    print("\n=== 记忆系统测试 ===")
    
    try:
        from app.memory import get_memory_manager
        mm = get_memory_manager("test_user", "test_thread")
        
        # 测试消息存储
        mm.save_message("user", "测试消息")
        messages = mm.get_messages()
        assert len(messages) == 1
        
        # 测试偏好存储
        mm.save_user_preference("resume_style", "technical")
        pref = mm.get_user_preference("resume_style")
        assert pref == "technical"
        
        # 测试工作记忆
        mm.set_working_memory("key", "value")
        val = mm.get_working_memory("key")
        assert val == "value"
        
        print("  memory_system: OK")
        return 1
    except Exception as e:
        print(f"  memory_system: FAIL - {e}")
        return 0

def test_module_imports():
    """测试模块导入"""
    print("\n=== 模块导入测试 ===")
    
    modules = [
        "app.main",
        "app.database",
        "app.auth",
        "app.models.user",
        "app.schemas.user",
        "app.routers.agents",
        "app.graphs.resume_workflow",
        "app.memory.manager",
    ]
    
    passed = 0
    for mod in modules:
        try:
            __import__(mod)
            print(f"  {mod}: OK")
            passed += 1
        except Exception as e:
            print(f"  {mod}: FAIL - {str(e)[:50]}")
    
    return passed

if __name__ == "__main__":
    print("=" * 50)
    print("Career Co-Pilot 全面功能测试")
    print("=" * 50)
    
    results = {
        "api_routes": test_api_routes(),
        "database_models": test_database_models(),
        "agent_tools": test_agent_tools(),
        "workflow": test_workflow(),
        "memory_system": test_memory_system(),
        "module_imports": test_module_imports(),
    }
    
    print("\n" + "=" * 50)
    print("测试汇总")
    print("=" * 50)
    total = 0
    passed = 0
    for name, result in results.items():
        status = "PASS" if result > 0 else "FAIL"
        print(f"  {name}: {status} ({result})")
        total += 1
        if result > 0:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
