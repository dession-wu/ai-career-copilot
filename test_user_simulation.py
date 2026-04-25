"""
用户模拟测试 - 验证PDF解析和个人信息提取的准确度与完整度
模拟真实用户上传简历后的使用场景
"""

import sys
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# ============ 模拟简历数据 ============

SAMPLE_RESUMES = [
    {
        "name": "简历1-标准格式",
        "content": """张三
手机：13800138000 | 邮箱：zhangsan@example.com | 微信：zs123456
北京市海淀区

教育背景
2018.09-2022.06 北京大学 计算机科学与技术 本科
2022.09-2025.06 清华大学 软件工程 硕士

工作经历
2023.07-至今 阿里巴巴 高级Java开发工程师
负责淘宝核心交易系统开发

技能
Java、Spring Boot、MySQL、Redis、Docker、Kubernetes

项目经历
双11大促系统优化
负责性能优化，QPS提升300%""",
        "expected": {
            "name": "张三",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "education_count": 2,
            "work_count": 1,
            "skill_count": 6,
            "project_count": 1
        }
    },
    {
        "name": "简历2-带特殊分隔符",
        "content": """李四
手机：13900139000丨邮箱：lisi@163.com丨地址：上海市浦东新区

教育经历
2019.09-2023.07 复旦大学 金融学 本科 GPA:3.8/4.0

工作实践
2023.08-2024.12 华泰证券 投资分析师
2025.01-至今 中信证券 高级投资经理

专业技能
熟练掌握Python、R语言、MATLAB、Tableau、Excel数据分析
精通财务建模、估值分析、行业研究

主要项目
新能源汽车行业研究报告
负责产业链分析和公司估值""",
        "expected": {
            "name": "李四",
            "phone": "13900139000",
            "email": "lisi@163.com",
            "education_count": 1,
            "work_count": 2,
            "skill_count": 8,  # Python, R, MATLAB, Tableau, Excel + 财务建模等
            "project_count": 1
        }
    },
    {
        "name": "简历3-设计类",
        "content": """王五
电话：13700137000
邮箱：wangwu@gmail.com
作品集：www.wangwu.design

教育背景
2017.09-2021.06 中国美术学院 视觉传达设计 本科

工作经历
2021.07-2023.05 字节跳动 UI设计师
2023.06-至今 腾讯 高级视觉设计师

技能清单
PS/PR/AI/AE、Figma、Sketch、C4D、Blender
UI设计、动效设计、品牌设计、三维设计

项目经验
抖音短视频编辑器设计
负责核心交互和视觉设计""",
        "expected": {
            "name": "王五",
            "phone": "13700137000",
            "email": "wangwu@gmail.com",
            "education_count": 1,
            "work_count": 2,
            "skill_count": 10,  # PS, PR, AI, AE, Figma, Sketch, C4D, Blender + 设计类型
            "project_count": 1
        }
    },
    {
        "name": "简历4-复杂格式",
        "content": """赵六
联系方式：13600136000 / zhaoliu@qq.com
现居：广州市天河区

【教育背景】
2020.09-2024.07
华南理工大学
环境工程 本科
主修课程：环境监测、污染控制工程

【实习经历】
2023.07-2023.09
宝洁公司
供应链实习生

【校园经历】
学生会主席
环保社团创始人

【技能证书】
CET-6（580分）
计算机二级
驾驶证C1
熟练掌握ArcGIS、Origin、AutoCAD、Office办公软件""",
        "expected": {
            "name": "赵六",
            "phone": "13600136000",
            "email": "zhaoliu@qq.com",
            "education_count": 1,
            "work_count": 1,  # 实习经历
            "skill_count": 6,  # CET-6, 计算机二级, 驾驶证, ArcGIS, Origin, AutoCAD, Office
            "project_count": 0
        }
    },
    {
        "name": "简历5-极简格式",
        "content": """陈七
13100131000
chenqi@outlook.com

清华大学 博士 人工智能
2020-2024

Google 研究员
2024-至今

Python PyTorch TensorFlow
发表SCI论文5篇""",
        "expected": {
            "name": "陈七",
            "phone": "13100131000",
            "email": "chenqi@outlook.com",
            "education_count": 1,
            "work_count": 1,
            "skill_count": 3,
            "project_count": 0
        }
    }
]


# ============ 技能词库（复制自config.py） ============

SKILL_CATEGORIES = {
    "programming_languages": {
        "keywords": ["Python", "Java", "R", "MATLAB", "SQL", "C++", "JavaScript"],
        "aliases": {"R": ["R语言"], "Python": ["Py"], "JavaScript": ["JS"]}
    },
    "data_analysis": {
        "keywords": ["Tableau", "Origin", "SPSS", "Excel数据分析", "Pandas"],
        "aliases": {}
    },
    "gis": {
        "keywords": ["ArcGIS", "QGIS", "ENVI"],
        "aliases": {}
    },
    "design": {
        "keywords": ["Photoshop", "Premiere", "Illustrator", "After Effects", "Figma", "Sketch", "C4D", "Blender", "AutoCAD"],
        "aliases": {
            "Photoshop": ["PS"],
            "Premiere": ["PR"],
            "Illustrator": ["AI"],
            "After Effects": ["AE"],
            "AutoCAD": ["CAD"]
        }
    },
    "office": {
        "keywords": ["Microsoft Office", "Word", "Excel", "PowerPoint"],
        "aliases": {"Microsoft Office": ["Office", "办公软件"]}
    },
    "ai_ml": {
        "keywords": ["PyTorch", "TensorFlow", "Keras", "Scikit-learn"],
        "aliases": {}
    }
}

SKILL_ALIASES = {}
for category, config in SKILL_CATEGORIES.items():
    if "aliases" in config:
        for standard_name, aliases in config["aliases"].items():
            SKILL_ALIASES[standard_name.lower()] = standard_name
            for alias in aliases:
                SKILL_ALIASES[alias.lower()] = standard_name


# ============ 提取函数 ============

def extract_name(text: str) -> Optional[str]:
    """提取姓名 - 通常在开头的前几行"""
    lines = text.split('\n')[:5]  # 检查前5行
    
    for line in lines:
        line = line.strip()
        # 中文姓名：2-4个汉字
        if re.match(r'^[\u4e00-\u9fa5]{2,4}$', line):
            return line
        # 英文姓名
        if re.match(r'^[A-Za-z]+\s+[A-Za-z]+$', line):
            return line
    return None


def extract_phone(text: str) -> Optional[str]:
    """提取电话"""
    # 中国大陆手机号
    pattern = r'1[3-9]\d{9}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_email(text: str) -> Optional[str]:
    """提取邮箱 - 增强版本"""
    # 清理特殊分隔符
    cleaned_text = text.replace('丨', ' ').replace('|', ' ').replace('/', ' ')
    
    # 标准邮箱模式
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    match = re.search(pattern, cleaned_text)
    if match:
        return match.group(0)
    
    # 宽松模式
    loose_pattern = r'[\s丨|/]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})[\s丨|/]*'
    match = re.search(loose_pattern, text)
    if match:
        return match.group(1)
    
    return None


def extract_education(text: str) -> List[Dict]:
    """提取教育经历 - 增强版本，支持极简格式"""
    education_list = []
    
    # 查找教育相关章节
    edu_patterns = [
        r'(?:教育背景|教育经历|学历|教育)[\s\n]*(.+?)(?=\n\n|\n(?:工作|项目|技能)|$)',
        r'(?:EDUCATION|Academic Background)[\s\n]*(.+?)(?=\n\n|\n(?:WORK|EXPERIENCE)|$)'
    ]
    
    for pattern in edu_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            edu_section = match.group(1)
            
            # 提取学校（包含大学、学院、学校等关键词）
            school_pattern = r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))'
            schools = re.findall(school_pattern, edu_section)
            
            for school in schools:
                education_list.append({"school": school})
    
    # 如果没有找到教育章节，尝试极简格式解析
    if not education_list:
        # 查找包含大学/学院/学校的行
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # 匹配学校名称
            school_match = re.search(r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校|University|College))', line, re.IGNORECASE)
            if school_match:
                education_list.append({"school": school_match.group(1)})
            # 匹配学历关键词（如"博士"、"硕士"、"本科"）
            elif re.search(r'(博士|硕士|本科|Bachelor|Master|PhD)', line, re.IGNORECASE):
                # 检查前一行是否是学校
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if len(prev_line) > 2 and len(prev_line) < 50:
                        education_list.append({"school": prev_line})
    
    return education_list


def extract_work_experience(text: str) -> List[Dict]:
    """提取工作经历 - 增强版本"""
    work_list = []
    
    # 查找工作相关章节
    work_patterns = [
        r'(?:工作经历|工作经验|工作实践|实习经历)[\s\n]*(.+?)(?=\n\n|\n(?:教育|项目|技能)|$)',
        r'(?:WORK EXPERIENCE|Experience)[\s\n]*(.+?)(?=\n\n|\n(?:EDUCATION|PROJECT)|$)'
    ]
    
    for pattern in work_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            work_section = match.group(1)
            
            # 提取公司 - 扩展匹配模式
            company_patterns = [
                r'([\u4e00-\u9fa5]{2,30}(?:公司|集团))',
                r'([\u4e00-\u9fa5]{2,20}(?:科技|网络|软件|信息|技术))',
                r'\b(阿里巴巴|腾讯|字节跳动|百度|美团|京东|滴滴|快手|拼多多|网易|小米|华为|Google|Microsoft|Amazon|Facebook|Meta|Apple)\b',
                r'([\u4e00-\u9fa5]{2,20}(?:证券|银行|保险|基金|投资))',
            ]
            
            for company_pattern in company_patterns:
                companies = re.findall(company_pattern, work_section, re.IGNORECASE)
                for company in companies:
                    if company not in [w["company"] for w in work_list]:
                        work_list.append({"company": company})
            
            # 如果没有找到公司，尝试提取第一行作为公司
            if not work_list:
                lines = work_section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if 2 < len(line) < 40 and not re.match(r'^\d{4}', line):
                        # 排除纯日期行
                        work_list.append({"company": line})
                        break
    
    return work_list


def normalize_skill_name(skill_name: str) -> str:
    """标准化技能名称"""
    skill_lower = skill_name.lower().strip()
    if skill_lower in SKILL_ALIASES:
        return SKILL_ALIASES[skill_lower]
    return skill_name


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


def extract_skills(text: str) -> List[str]:
    """提取技能 - 增强版本"""
    skills = []
    found_skills = set()
    
    # 查找技能相关章节
    skill_section = ""
    skill_patterns = [
        r'(?:技能|技能清单|专业技能|技术栈)[\s\n]*(.+?)(?=\n\n|\n(?:教育|工作|项目)|$)',
        r'(?:SKILLS|Technical Skills)[\s\n]*(.+?)(?=\n\n|\n(?:EDUCATION|WORK)|$)'
    ]
    
    for pattern in skill_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skill_section = match.group(1)
            break
    
    if not skill_section:
        skill_section = text  # 如果没有找到技能章节，搜索全文
    
    # 方法1：使用词库匹配
    for category, config in SKILL_CATEGORIES.items():
        for skill in config["keywords"]:
            # 单词边界匹配
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, skill_section, re.IGNORECASE):
                normalized = normalize_skill_name(skill)
                if normalized.lower() not in found_skills:
                    found_skills.add(normalized.lower())
                    skills.append(normalized)
        
        # 检查别名
        if "aliases" in config:
            for standard_name, aliases in config["aliases"].items():
                for alias in aliases:
                    pattern = rf'\b{re.escape(alias)}\b'
                    if re.search(pattern, skill_section, re.IGNORECASE):
                        if standard_name.lower() not in found_skills:
                            found_skills.add(standard_name.lower())
                            if standard_name not in skills:
                                skills.append(standard_name)
    
    # 方法2：解析列表格式
    # 移除熟练度前缀
    cleaned_section = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', skill_section)
    
    # 尝试多种分隔符
    separators = ['、', '，', ',', ';', '；', '|', '/', '\n']
    for sep in separators:
        if sep in cleaned_section:
            items = cleaned_section.split(sep)
            for item in items:
                item = item.strip()
                item = re.sub(r'^[•\-\*・\s]+', '', item).strip()
                item = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', item)
                if item and 1 < len(item) < 30:
                    normalized = normalize_skill_name(item)
                    if normalized.lower() not in found_skills:
                        # 检查是否是已知技能
                        for category, config in SKILL_CATEGORIES.items():
                            keywords_lower = [k.lower() for k in config["keywords"]]
                            aliases_lower = []
                            if "aliases" in config:
                                for aliases in config["aliases"].values():
                                    aliases_lower.extend([a.lower() for a in aliases])
                            
                            if normalized.lower() in keywords_lower or normalized.lower() in aliases_lower:
                                found_skills.add(normalized.lower())
                                skills.append(normalized)
                                break
            break
    
    # 方法3：提取组合技能（如PS/PR）
    combo_skills = extract_combo_skills(skill_section)
    for skill in combo_skills:
        if skill.lower() not in found_skills:
            found_skills.add(skill.lower())
            skills.append(skill)
    
    # 方法4：全文扫描补充（如果技能太少）
    if len(skills) < 3:
        for category, config in SKILL_CATEGORIES.items():
            for skill in config["keywords"]:
                pattern = rf'\b{re.escape(skill)}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    normalized = normalize_skill_name(skill)
                    if normalized.lower() not in found_skills:
                        found_skills.add(normalized.lower())
                        skills.append(normalized)
    
    return skills


def extract_projects(text: str) -> List[Dict]:
    """提取项目经历"""
    project_list = []
    
    # 查找项目相关章节
    project_patterns = [
        r'(?:项目经历|项目经验|主要项目)[\s\n]*(.+?)(?=\n\n|\n(?:教育|工作|技能)|$)',
        r'(?:PROJECTS|Project Experience)[\s\n]*(.+?)(?=\n\n|\n(?:EDUCATION|WORK)|$)'
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            project_section = match.group(1)
            
            # 按段落分割
            paragraphs = re.split(r'\n\n+', project_section.strip())
            for para in paragraphs:
                para = para.strip()
                if para and len(para) > 10:
                    # 提取项目名称（第一行）
                    lines = para.split('\n')
                    if lines:
                        project_name = lines[0].strip()
                        # 清理列表符号
                        project_name = re.sub(r'^[•\-\*・《]', '', project_name).strip()
                        if project_name and len(project_name) < 100:
                            project_list.append({"name": project_name})
    
    return project_list


# ============ 测试评估 ============

@dataclass
class ExtractionResult:
    """提取结果"""
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    education: List[Dict]
    work_experience: List[Dict]
    skills: List[str]
    projects: List[Dict]
    
    def calculate_accuracy(self, expected: Dict) -> Dict[str, float]:
        """计算准确度"""
        scores = {}
        
        # 姓名准确度
        scores["name"] = 1.0 if self.name == expected["name"] else 0.0
        
        # 电话准确度
        scores["phone"] = 1.0 if self.phone == expected["phone"] else 0.0
        
        # 邮箱准确度
        scores["email"] = 1.0 if self.email == expected["email"] else 0.0
        
        # 教育经历完整度
        edu_ratio = len(self.education) / max(expected["education_count"], 1)
        scores["education"] = min(edu_ratio, 1.0)
        
        # 工作经历完整度
        work_ratio = len(self.work_experience) / max(expected["work_count"], 1)
        scores["work"] = min(work_ratio, 1.0)
        
        # 技能完整度
        skill_ratio = len(self.skills) / max(expected["skill_count"], 1)
        scores["skills"] = min(skill_ratio, 1.0)
        
        # 项目完整度
        project_ratio = len(self.projects) / max(expected["project_count"], 1)
        scores["projects"] = min(project_ratio, 1.0)
        
        return scores
    
    def get_overall_score(self, expected: Dict) -> float:
        """获取总体评分"""
        scores = self.calculate_accuracy(expected)
        return sum(scores.values()) / len(scores)


def parse_resume(text: str) -> ExtractionResult:
    """解析简历"""
    return ExtractionResult(
        name=extract_name(text),
        phone=extract_phone(text),
        email=extract_email(text),
        education=extract_education(text),
        work_experience=extract_work_experience(text),
        skills=extract_skills(text),
        projects=extract_projects(text)
    )


def run_user_simulation():
    """运行用户模拟测试"""
    print("=" * 80)
    print("用户模拟测试 - PDF解析和个人信息提取准确度验证")
    print("=" * 80)
    
    results = []
    
    for i, resume_data in enumerate(SAMPLE_RESUMES, 1):
        print(f"\n{'='*80}")
        print(f"测试简历 {i}: {resume_data['name']}")
        print("=" * 80)
        
        # 解析简历
        result = parse_resume(resume_data['content'])
        expected = resume_data['expected']
        
        # 显示提取结果
        print("\n提取结果:")
        print(f"  姓名: {result.name} (期望: {expected['name']})")
        print(f"  电话: {result.phone} (期望: {expected['phone']})")
        print(f"  邮箱: {result.email} (期望: {expected['email']})")
        print(f"  教育经历: {len(result.education)} 条 (期望: {expected['education_count']})")
        print(f"  工作经历: {len(result.work_experience)} 条 (期望: {expected['work_count']})")
        print(f"  技能: {len(result.skills)} 个 (期望: {expected['skill_count']})")
        print(f"  项目: {len(result.projects)} 个 (期望: {expected['project_count']})")
        
        if result.skills:
            print(f"  技能列表: {', '.join(result.skills)}")
        
        # 计算准确度
        scores = result.calculate_accuracy(expected)
        overall_score = result.get_overall_score(expected)
        
        print(f"\n准确度评分:")
        for field, score in scores.items():
            status = "✓" if score == 1.0 else "⚠" if score >= 0.5 else "✗"
            print(f"  {status} {field}: {score*100:.1f}%")
        
        print(f"\n总体评分: {overall_score*100:.1f}%")
        
        results.append({
            "name": resume_data['name'],
            "score": overall_score,
            "details": scores
        })
    
    # 汇总
    print(f"\n{'='*80}")
    print("测试汇总")
    print("=" * 80)
    
    avg_score = sum(r['score'] for r in results) / len(results)
    
    print(f"\n总体平均准确度: {avg_score*100:.1f}%")
    print("\n各简历评分:")
    for r in results:
        status = "✓" if r['score'] >= 0.8 else "⚠" if r['score'] >= 0.6 else "✗"
        print(f"  {status} {r['name']}: {r['score']*100:.1f}%")
    
    # 评估
    print(f"\n{'='*80}")
    print("评估结论")
    print("=" * 80)
    
    if avg_score >= 0.8:
        print("✓ 准确度优秀 (>= 80%)，无需修复")
    elif avg_score >= 0.6:
        print("⚠ 准确度一般 (60-80%)，建议优化")
    else:
        print("✗ 准确度较低 (< 60%)，需要修复")
    
    # 问题诊断
    print("\n问题诊断:")
    field_scores = {}
    for r in results:
        for field, score in r['details'].items():
            if field not in field_scores:
                field_scores[field] = []
            field_scores[field].append(score)
    
    avg_field_scores = {f: sum(s)/len(s) for f, s in field_scores.items()}
    
    for field, score in sorted(avg_field_scores.items(), key=lambda x: x[1]):
        if score < 0.8:
            print(f"  ⚠ {field}: 平均准确度 {score*100:.1f}% - 需要改进")
    
    return avg_score


if __name__ == "__main__":
    score = run_user_simulation()
    sys.exit(0 if score >= 0.6 else 1)
