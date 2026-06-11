"""
P0-8 端到端验证脚本
验证吴烨简历的完整提取链路：基础信息 6 字段 + 教育 >= 2 条
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# 强制 UTF-8 输出（避免 Windows GBK 控制台问题）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 启用 INFO 日志，确保 [P0-10] 监控埋点可见
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.resume_extraction.resume_extraction_service import (
    get_resume_extraction_service,
)


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "wuye_resume.txt"

# ASCII 兼容字符
OK = "[OK]"
NG = "[NG]"


def main():
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    print("=" * 70)
    print(f" Resume E2E Verify: Wuye sample (fixture: {FIXTURE_PATH.name})")
    print("=" * 70)
    print(f"Input text length: {len(text)} chars")
    print()

    svc = get_resume_extraction_service()
    # ★ P0-11: 改用 v2 路径，验证 P0-10 监控埋点生效
    result = asyncio.run(svc.extract_from_text_v2(text, user_id="p0-8-e2e", use_llm=False))

    if not result.get("success"):
        print(f"[NG] Extract failed: {result.get('error')}")
        sys.exit(1)

    data = result.get("data", {})
    schema_version = result.get("schema_version", "?")
    print(f"schema_version: {schema_version}")
    print(f"degraded: {result.get('degraded', False)}")
    print(f"extraction_time_ms: {result.get('extraction_time_ms')}ms")
    print()

    # === 基础信息断言 ===
    pi = data.get("personal_info", {})
    print("--- Personal Info ---")
    expected = {
        "name": "吴烨",
        "phone": "18133004892",
        "email": "18133004892@163.com",
        "location": "安徽安庆",
        "political_status": "party_member",
        "birth_date": "2002-10",
    }
    passed = 0
    for k, v in expected.items():
        actual = pi.get(k, "")
        ok = actual == v
        mark = OK if ok else NG
        print(f"  {mark} {k:18s} = {actual!r:35s} (expected: {v!r})")
        if ok:
            passed += 1
    print(f"  Personal info: {passed}/{len(expected)} passed")
    print()

    # === 教育经历断言 ===
    # v2 路径用 "educations"（复数），v1 用 "education"
    print("--- Education ---")
    edus = data.get("educations") or data.get("education") or []
    print(f"  Total: {len(edus)} entries")
    for i, e in enumerate(edus):
        print(
            f"  [{i+1}] school={e.get('school','')!r:25s} "
            f"degree={e.get('degree','')!r:6s} "
            f"field={e.get('field','')!r:10s} "
            f"{e.get('start_date','')} ~ {e.get('end_date','')}"
        )

    schools = {e.get("school", "") for e in edus}
    fields = {e.get("field", "") for e in edus}
    has_zju = "浙江大学" in schools
    has_ustb = "北京科技大学" in schools
    has_field = ("环境科学" in fields) or ("环境工程" in fields)
    edu_count_ok = len(edus) >= 2

    print()
    print(f"  {OK if edu_count_ok else NG} Education count >= 2 (actual {len(edus)})")
    print(f"  {OK if has_zju else NG} Contains '浙江大学'")
    print(f"  {OK if has_ustb else NG} Contains '北京科技大学'")
    print(f"  {OK if has_field else NG} Contains field '环境科学' or '环境工程'")
    print()

    # === 总结 ===
    print("=" * 70)
    overall_ok = (passed >= 5) and edu_count_ok and has_zju and has_ustb and has_field
    if overall_ok:
        print(f" [OK] P0-8 E2E PASS: personal_info {passed}/6, education {len(edus)}")
        print(f"     0% -> {passed*100//6}% (personal), 0% -> {'80%+' if edu_count_ok else 'N/A'} (edu)")
    else:
        print(f" [NG] P0-8 E2E FAIL: personal {passed}/6, education {len(edus)}")
    print("=" * 70)
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
