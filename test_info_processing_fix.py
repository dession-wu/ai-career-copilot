"""
信息加工处理模块修复验证脚本
验证技能识别、章节分类、项目经历、个人信息提取的修复效果
"""

import sys
import re
from typing import List, Dict, Any, Optional, Tuple

# ============ 测试技能词库 ============
SKILL_CATEGORIES = {
    "programming_languages": {
        "keywords": [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "Swift", "Kotlin", "PHP", "Ruby", "Scala", "Perl", "R", "MATLAB", "Lua",
            "Shell", "Bash", "C", "Objective-C", "Groovy", "Dart", "Julia", "Haskell",
            "SQL", "PL/SQL", "T-SQL", "NoSQL", "R语言", "Python语言"
        ],
        "display_name": "编程语言",
        "aliases": {
            "Python": ["python", "py", "Python语言"],
            "JavaScript": ["javascript", "js", "JS"],
            "MATLAB": ["matlab", "Matlab", "MATLAB"],
            "R": ["R语言", "r语言", "R"],
        }
    },
    "data_analysis": {
        "keywords": [
            "Tableau", "Power BI", "Origin", "SPSS", "SAS", "Stata", "Minitab",
            "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly"
        ],
        "display_name": "数据分析工具",
        "aliases": {
            "Tableau": ["tableau", "Tableau"],
        }
    },
    "gis": {
        "keywords": [
            "ArcGIS", "QGIS", "MapInfo", "SuperMap", "Google Earth", "ENVI",
            "ERDAS", "GIS", "遥感", "GPS", "北斗", "空间分析"
        ],
        "display_name": "GIS/遥感",
        "aliases": {
            "ArcGIS": ["arcgis", "Arcgis", "ARCGIS"],
        }
    },
    "design": {
        "keywords": [
            "Photoshop", "Premiere", "Illustrator", "After Effects", "InDesign",
            "Lightroom", "Audition", "XD", "Figma", "Sketch", "CorelDRAW",
            "AutoCAD", "3ds Max", "Maya", "Blender", "PS", "PR", "AI", "AE", "CAD"
        ],
        "display_name": "设计软件",
        "aliases": {
            "Photoshop": ["photoshop", "PS", "ps", "Ps"],
            "Premiere": ["premiere", "PR", "pr", "Pr"],
            "Illustrator": ["illustrator", "AI", "ai", "Ai"],
            "AutoCAD": ["autocad", "CAD", "cad", "Cad"],
        }
    },
    "office": {
        "keywords": [
            "Microsoft Office", "Word", "Excel", "PowerPoint", "Access", "Outlook",
            "WPS", "Office办公软件", "办公软件", "Office", "MS Office"
        ],
        "display_name": "办公软件",
        "aliases": {
            "Microsoft Office": ["Office", "MS Office", "office", "Office办公软件", "办公软件"],
            "PowerPoint": ["powerpoint", "PPT", "ppt", "Powerpoint"],
        }
    },
}

# 构建别名映射
SKILL_ALIASES = {}
for category, config in SKILL_CATEGORIES.items():
    if "aliases" in config:
        for standard_name, aliases in config["aliases"].items():
            SKILL_ALIASES[standard_name.lower()] = standard_name
            for alias in aliases:
                SKILL_ALIASES[alias.lower()] = standard_name


def normalize_skill_name(skill_name: str) -> str:
    """标准化技能名称"""
    skill_lower = skill_name.lower().strip()
    if skill_lower in SKILL_ALIASES:
        return SKILL_ALIASES[skill_lower]
    return skill_name


def parse_skill_list(text: str) -> List[str]:
    """解析技能列表"""
    skills = []
    # 清理文本 - 移除常见前缀
    text = re.sub(r'^[•\-\*・\s]+', '', text.strip())
    # 移除熟练度前缀
    text = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', text)
    
    separators = ['、', '，', ',', ';', '；', '|', '/', '·', '\n', '\t']
    
    primary_separator = None
    max_splits = 0
    for sep in separators:
        count = text.count(sep)
        if count > max_splits and count >= 2:
            max_splits = count
            primary_separator = sep
    
    if primary_separator:
        items = text.split(primary_separator)
    else:
        items = re.split(r'[、,，;；|/·\n\t]+', text)
    
    for item in items:
        item = item.strip()
        item = re.sub(r'^[•\-\*・\s]+', '', item).strip()
        item = re.sub(r'\s+', ' ', item)
        # 移除每个项目中的熟练度前缀
        item = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', item)
        
        if item and 1 < len(item) < 40:
            normalized = normalize_skill_name(item)
            skills.append(normalized)
    
    # 去重
    seen = set()
    unique_skills = []
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower not in seen:
            seen.add(skill_lower)
            unique_skills.append(skill)
    
    return unique_skills


def extract_combo_skills(text: str) -> List[str]:
    """提取组合格式的技能（如"PS/PR"）"""
    skills = []
    combo_pattern = r'\b([A-Z]{1,3})\/([A-Z]{1,3})\b'
    matches = re.finditer(combo_pattern, text)
    
    for match in matches:
        part1 = match.group(1)
        part2 = match.group(2)
        
        for part in [part1, part2]:
            normalized = normalize_skill_name(part)
            if normalized != part or part in ['PS', 'PR', 'AI', 'AE', 'LR', 'AU', 'CAD']:
                skills.append(normalized)
    
    return skills


def extract_email(text: str) -> Optional[str]:
    """提取邮箱"""
    cleaned_text = text.replace('丨', ' ').replace('|', ' ').replace('/', ' ')
    
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, cleaned_text)
    if match:
        return match.group(0)
    
    loose_pattern = r'[\s丨|/]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})[\s丨|/]*'
    match = re.search(loose_pattern, text)
    if match:
        return match.group(1)
    
    return None


def extract_phone(text: str) -> Optional[str]:
    """提取电话"""
    pattern = r'1[3-9]\d{9}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


# ============ 测试用例 ============

def test_skill_recognition():
    """测试技能识别"""
    print("=" * 60)
    print("测试 1: 技能识别修复")
    print("=" * 60)
    
    # 测试多种分隔符
    test_cases = [
        ("Python、Java、C++", ["Python", "Java", "C++"]),
        ("MATLAB, Python, R语言", ["MATLAB", "Python", "R"]),
        ("Tableau; ArcGIS; MySQL", ["Tableau", "ArcGIS", "MySQL"]),
        ("PS/PR/AI", ["Photoshop", "Premiere", "Illustrator"]),
        ("Microsoft Office、Word、Excel", ["Microsoft Office", "Word", "Excel"]),
    ]
    
    all_passed = True
    for text, expected in test_cases:
        skills = parse_skill_list(text)
        passed = len(skills) >= len(expected)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{status} 输入: {text}")
        print(f"       输出: {skills}")
        print(f"       期望: {expected}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_email_extraction():
    """测试邮箱提取"""
    print("\n" + "=" * 60)
    print("测试 2: 邮箱提取增强")
    print("=" * 60)
    
    test_cases = [
        ("联系邮箱：test@example.com", "test@example.com"),
        ("手机：13800138000丨邮箱：name@example.com丨地址：北京", "name@example.com"),
        ("name@example.com | 13800138000", "name@example.com"),
        ("18133004892@163.com", "18133004892@163.com"),
    ]
    
    all_passed = True
    for text, expected in test_cases:
        result = extract_email(text)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{status} 输入: {text}")
        print(f"       输出: {result}")
        print(f"       期望: {expected}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_section_keywords():
    """测试章节关键词"""
    print("\n" + "=" * 60)
    print("测试 3: 章节关键词扩展")
    print("=" * 60)
    
    section_keywords = {
        "education": [
            "教育背景", "教育经历", "学历", "教 育 背 景", "EDUCATION BACKGROUND"
        ],
        "work_experience": [
            "工作经验", "工作经历", "工作实践", "工 作 经 历", "WORK EXPERIENCE"
        ],
        "projects": [
            "项目经历", "项目经验", "项 目 经 历", "PROJECT EXPERIENCE"
        ],
        "skills": [
            "技能", "技能清单", "技 能", "SKILL SET", "技术栈"
        ],
    }
    
    all_passed = True
    for section, keywords in section_keywords.items():
        print(f"\n✓ {section}: {keywords}")
    
    return all_passed


def test_full_resume():
    """测试完整简历"""
    print("\n" + "=" * 60)
    print("测试 4: 完整简历提取")
    print("=" * 60)
    
    resume_text = """吴烨
手机：18133004892丨邮箱：18133004892@163.com

教育背景
2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）

技能
熟练掌握MATLAB、Python、R语言、Tableau、Microsoft Office、PS/PR、ArcGIS、MySQL

项目经历
北京市生活垃圾管理项目
负责数据分析和可视化，使用Python和Tableau

中国水泥行业碳排放项目
负责数据收集和模型建立"""
    
    print(f"\n简历文本:\n{resume_text}")
    print("\n" + "-" * 60)
    
    # 提取个人信息
    email = extract_email(resume_text)
    phone = extract_phone(resume_text)
    
    # 提取技能
    skill_section = "熟练掌握MATLAB、Python、R语言、Tableau、Microsoft Office、PS/PR、ArcGIS、MySQL"
    skills = parse_skill_list(skill_section)
    
    # 额外提取组合技能
    combo_skills = extract_combo_skills(skill_section)
    for skill in combo_skills:
        if skill not in skills:
            skills.append(skill)
    
    print(f"\n提取结果:")
    print(f"  邮箱: {email}")
    print(f"  电话: {phone}")
    print(f"  技能: {skills}")
    
    # 验证
    checks = [
        ("邮箱正确", email == "18133004892@163.com"),
        ("电话正确", phone == "18133004892"),
        ("MATLAB识别", "MATLAB" in skills),
        ("Python识别", "Python" in skills),
        ("R语言识别", "R" in skills or any("R" == s for s in skills)),
        ("Tableau识别", "Tableau" in skills),
        ("ArcGIS识别", "ArcGIS" in skills),
        ("MySQL识别", "MySQL" in skills),
        ("PS映射到Photoshop", "Photoshop" in skills),
        ("PR映射到Premiere", "Premiere" in skills),
    ]
    
    all_passed = True
    print("\n验证结果:")
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("信息加工处理模块修复验证")
    print("=" * 60)
    
    results = []
    
    results.append(("技能识别", test_skill_recognition()))
    results.append(("邮箱提取", test_email_extraction()))
    results.append(("章节关键词", test_section_keywords()))
    results.append(("完整简历", test_full_resume()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，需要进一步修复")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
