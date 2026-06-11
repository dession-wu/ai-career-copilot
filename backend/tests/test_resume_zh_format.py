"""
中文格式简历提取测试 — P0 止血测试集
基于吴烨真实简历 + 5 种典型变体

P0-7 目标：覆盖 P0-1 ~ P0-6 的所有修复
"""
import pytest
from app.services.resume_extraction.rule_engine import RuleEngine
from app.services.resume_extraction.layout_analyzer import LayoutAnalyzer
from app.services.resume_extraction.models import (
    ParsedDocument, DocumentStructure, PDFType, Section, SectionType,
)
from app.services.resume_extraction.resume_extraction_service import (
    ResumeExtractionService,
)


# ========== 测试样本 ==========

WUYE_RESUME = """
吴烨
中共党员丨2002.10丨安徽安庆
18133004892丨18133004892@163.com

教 育 背 景
2024.09-至今 浙江大学 环境科学（硕士）
2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）
2022.08-2023.01 华南理工大学（4.0/4.0） 环境工程（交流）

项 目 经 历
2023.07-2024.01 中国建设科技集团 《北京市生活垃圾管理全过程碳排放测算服务》

所 获 荣 誉
2022.10 北京科技大学 校级优秀学生干部
2021.10 北京科技大学 校级优秀团员

自 我 评 价
勤奋好学，责任心强，具有较强的团队合作精神。
"""


# 标准格式（用 | 分隔）
LI_BIAOZHUN_RESUME = """
李四
女 | 1998.05 | 北京
13800138000 | lis@example.com

教育背景
2016.09-2020.07 清华大学 计算机科学与技术 本科

工作经历
2020.07-2023.06 字节跳动 后端工程师
- 负责推荐系统
"""


# 中英混合
LI_MIXED_RESUME = """
Wang Wei
wangwei@163.com | 13912345678 | Shanghai

Education
2014-09 to 2018-07 Tsinghua University, Computer Science, Bachelor

Work Experience
2018-07 to Present ByteDance, Senior Engineer
"""


# 表格简历（仅模拟，不真正解析表格）
LI_TABLE_RESUME = """
| 姓名 | 张三 |
| 政治面貌 | 共青团员 |
| 出生日期 | 2000-01-15 |
| 邮箱 | zhangsan@qq.com |
| 电话 | 13600000000 |

教育经历
2018-2022 北京大学 软件工程 本科
"""


# 无标题（仅靠特征识别）
LI_NO_HEADER_RESUME = """
赵六
zhaoliu@gmail.com | 13500000000 | 广东深圳

2020.09 - 至今 哈尔滨工业大学（深圳） 计算机科学 硕士
2016.09 - 2020.07 东北大学 软件工程 本科
"""


SAMPLES = [
    ("wuye", WUYE_RESUME),
    ("biaozhun", LI_BIAOZHUN_RESUME),
    ("mixed", LI_MIXED_RESUME),
    ("table", LI_TABLE_RESUME),
    ("no_header", LI_NO_HEADER_RESUME),
]


def _make_doc(text: str) -> ParsedDocument:
    """构造 ParsedDocument 辅助函数"""
    return ParsedDocument(
        raw_text=text,
        full_text=text,
        pdf_type=PDFType.TEXT,
        page_count=1,
        text_blocks=[],
        image_blocks=[],
        metadata={"source": "test"},
    )


# ========== P0-6b 基础信息测试 ==========


@pytest.mark.parametrize("name,text", SAMPLES)
def test_personal_info_name_extraction(name, text):
    """基础信息：姓名至少识别"""
    rule = RuleEngine()
    result = rule.extract(_make_doc(text), DocumentStructure(sections=[]))
    pi = result["personal_info"]
    assert pi.name, f"[{name}] 期望姓名非空，实际='{pi.name}'"


def test_wuye_basic_info_all_fields():
    """吴烨样本：基础信息 6 字段全验证 (P0-6b)"""
    rule = RuleEngine()
    result = rule.extract(_make_doc(WUYE_RESUME), DocumentStructure(sections=[]))
    pi = result["personal_info"]
    assert pi.name == "吴烨", f"姓名错误: {pi.name}"
    assert pi.email == "18133004892@163.com", f"邮箱错误: {pi.email}"
    assert pi.phone == "18133004892", f"电话错误: {pi.phone}"
    assert pi.political_status == "party_member", f"政治面貌错误: {pi.political_status}"
    assert pi.birth_date == "2002-10", f"出生日期错误: {pi.birth_date}"
    assert pi.location == "安徽安庆", f"所在地错误: {pi.location}"


def test_wuye_political_and_demographics():
    """吴烨样本：政治面貌/出生年月/籍贯独立验证"""
    rule = RuleEngine()
    result = rule.extract(_make_doc(WUYE_RESUME), DocumentStructure(sections=[]))
    pi = result["personal_info"]
    # 内部 dict 验证
    pi_dict = pi.to_dict()
    assert pi_dict["political_status"] == "party_member"
    assert pi_dict["birth_date"] == "2002-10"
    assert pi_dict["location"] == "安徽安庆"
    # 年龄推算
    assert pi.age is None or (20 <= pi.age <= 30), f"年龄推算异常: {pi.age}"


def test_li_biaozhun_political_status():
    """标准格式样本：李四（女/1998.05/北京）应识别 location"""
    rule = RuleEngine()
    result = rule.extract(_make_doc(LI_BIAOZHUN_RESUME), DocumentStructure(sections=[]))
    pi = result["personal_info"]
    assert pi.name == "李四"
    assert pi.email == "lis@example.com"
    assert pi.phone == "13800138000"
    # 1998.05 应被解析为出生日期
    assert pi.birth_date == "1998-05", f"李四 birth_date 错误: {pi.birth_date}"
    # 北京应被识别为 location
    assert pi.location == "北京", f"李四 location 错误: {pi.location}"


# ========== P0-5 教育提取测试 ==========


def test_wuye_education_extraction():
    """吴烨样本：教育经历至少 2 条（浙大 + 北科大）(P0-5)"""
    analyzer = LayoutAnalyzer()
    rule = RuleEngine()
    doc = _make_doc(WUYE_RESUME)
    structure = analyzer.analyze(doc)
    result = rule.extract(doc, structure)
    educations = result["education"]
    assert len(educations) >= 2, f"应≥2 条教育，实际={len(educations)}"
    schools = {e.school for e in educations}
    assert "浙江大学" in schools, f"应包含浙江大学，实际={schools}"
    assert "北京科技大学" in schools, f"应包含北京科技大学，实际={schools}"


def test_wuye_education_field_extraction():
    """吴烨样本：教育专业提取（环境科学/环境工程）(P0-5)"""
    rule = RuleEngine()
    section = Section(
        section_type=SectionType.EDUCATION,
        title="教育背景",
        content=(
            "2024.09-至今 浙江大学 环境科学（硕士）\n"
            "2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）"
        ),
        start_line=0,
        end_line=0,
    )
    entries = rule._extract_education(section)
    assert len(entries) >= 2, f"应≥2 条教育，实际={len(entries)}"
    fields = {e.field_of_study for e in entries if e.field_of_study}
    assert "环境科学" in fields or "环境工程" in fields, f"专业未提取: {fields}"


def test_education_strong_signal():
    """教育强信号：日期+学校 同时出现应被识别为教育（即使有"交流"等干扰词）"""
    rule = RuleEngine()
    section = Section(
        section_type=SectionType.EDUCATION,
        title="教育背景",
        content=(
            "2022.08-2023.01 华南理工大学（4.0/4.0） 环境工程（交流）\n"
            "2024.09-至今 浙江大学 环境科学（硕士）"
        ),
        start_line=0,
        end_line=0,
    )
    entries = rule._extract_education(section)
    schools = {e.school for e in entries}
    assert "华南理工大学" in schools, f"日期+学校应触发教育识别，实际={schools}"
    assert "浙江大学" in schools, f"标准格式应识别，实际={schools}"


def test_education_legend_school_university():
    """英文校名识别：University/College/Institute"""
    rule = RuleEngine()
    section = Section(
        section_type=SectionType.EDUCATION,
        title="Education",
        content=(
            "2014-09 to 2018-07 Tsinghua University, Computer Science, Bachelor\n"
            "2010-09 to 2014-07 Peking University, Software Engineering, Bachelor"
        ),
        start_line=0,
        end_line=0,
    )
    entries = rule._extract_education(section)
    schools = {e.school for e in entries}
    # 至少能识别出 University 后缀的英文校名
    assert any("University" in s for s in schools), f"应识别英文校名，实际={schools}"


# ========== P0-1 v2→v1 字段映射测试 ==========


def test_v2_to_v1_mapping():
    """v2→v1 字段映射（含日期规范化）(P0-1)"""
    v2_data = {
        "personal_info": {
            "name": "吴烨",
            "email": "18133004892@163.com",
            "phone": "18133004892",
            "location_city": "安徽安庆",
            "intent_position": "环境工程师",
            "political_status": "party_member",
        },
        "educations": [{
            "school": "浙江大学",
            "degree": "硕士",
            "field_of_study": "环境科学",
            "start_date": "2024.09",
            "end_date": "至今",
        }],
    }
    service = ResumeExtractionService()
    v1_data = service._v2_to_v1_compat(v2_data)
    assert v1_data["personal_info"]["location"] == "安徽安庆", \
        f"location 映射失败: {v1_data['personal_info']['location']}"
    assert v1_data["personal_info"]["job_intent"] == "环境工程师", \
        f"job_intent 映射失败: {v1_data['personal_info']['job_intent']}"
    assert v1_data["personal_info"]["political_status"] == "party_member", \
        f"political_status 映射失败: {v1_data['personal_info']['political_status']}"
    assert v1_data["education"][0]["field"] == "环境科学", \
        f"field 映射失败: {v1_data['education'][0]['field']}"
    assert v1_data["education"][0]["start_date"] == "2024-09", \
        f"start_date 规范化失败: {v1_data['education'][0]['start_date']}"
    assert v1_data["education"][0]["end_date"] == "至今", \
        f"end_date 保留 '至今' 失败: {v1_data['education'][0]['end_date']}"


def test_v2_to_v1_date_normalization():
    """v2→v1 日期规范化：YYYY.MM → YYYY-MM, YYYY年MM月 → YYYY-MM"""
    service = ResumeExtractionService()
    v2_data = {
        "personal_info": {},
        "educations": [
            {"school": "A", "start_date": "2020.09", "end_date": "2024.07"},
            {"school": "B", "start_date": "2020年9月", "end_date": "2024年07月"},
            {"school": "C", "start_date": "2020/09", "end_date": "2024-07"},
            {"school": "D", "start_date": "2020", "end_date": "至今"},
        ],
    }
    v1_data = service._v2_to_v1_compat(v2_data)
    assert v1_data["education"][0]["start_date"] == "2020-09"
    assert v1_data["education"][0]["end_date"] == "2024-07"
    assert v1_data["education"][1]["start_date"] == "2020-09"
    assert v1_data["education"][1]["end_date"] == "2024-07"
    assert v1_data["education"][2]["start_date"] == "2020-09"
    assert v1_data["education"][3]["end_date"] == "至今"


# ========== P0-4 layout_analyzer fallback 测试 ==========


def test_layout_analyzer_spaced_header():
    """layout_analyzer：识别带空格的章节标题 (P0-4)"""
    analyzer = LayoutAnalyzer()
    doc = _make_doc(WUYE_RESUME)
    structure = analyzer.analyze(doc)
    titles = [s.title for s in structure.sections]
    # 至少识别出教育章节（带空格的"教 育 背 景"）
    # 标题可能含空格，需要去空格后比较
    titles_normalized = [t.replace(' ', '').replace('\u3000', '') for t in titles]
    assert any("教育" in t for t in titles_normalized), \
        f"应识别教育章节（去空格后），实际 titles={titles}"


def test_layout_analyzer_fallback_for_no_header():
    """layout_analyzer：无标题简历的 fallback (P0-4)"""
    analyzer = LayoutAnalyzer()
    doc = _make_doc(LI_NO_HEADER_RESUME)
    structure = analyzer.analyze(doc)
    # 应能识别出教育章节（通过内容特征或 fallback）
    section_types = {s.section_type for s in structure.sections}
    assert SectionType.EDUCATION in section_types, \
        f"fallback 应识别教育章节，实际 types={section_types}"


# ========== 辅助：_normalize_local_date 单元测试 ==========


def test_normalize_local_date_various_formats():
    """_normalize_local_date 各种日期格式规范化"""
    from app.services.resume_extraction.rule_engine import _normalize_local_date
    # YYYY.MM → YYYY-MM
    assert _normalize_local_date("2024.09") == "2024-09"
    # YYYY/MM → YYYY-MM
    assert _normalize_local_date("2024/09") == "2024-09"
    # YYYY-MM 保持
    assert _normalize_local_date("2024-09") == "2024-09"
    # YYYY年MM月 → YYYY-MM
    assert _normalize_local_date("2024年9月") == "2024-09"
    assert _normalize_local_date("2024年09月") == "2024-09"
    # 至今 / Present 原样保留
    assert _normalize_local_date("至今") == "至今"
    assert _normalize_local_date("Present") == "Present"
    # YYYY → YYYY-01
    assert _normalize_local_date("2024") == "2024-01"
    # 空 / None
    assert _normalize_local_date("") == ""
    assert _normalize_local_date(None) == ""


# ========== PersonalInfo 新字段测试 ==========


def test_personal_info_new_fields():
    """PersonalInfo 新增 political_status, birth_date 字段 (P0-6a)"""
    from app.services.resume_extraction.models import PersonalInfo
    pi = PersonalInfo()
    # 默认值
    assert pi.political_status == ""
    assert pi.birth_date == ""
    # 赋值
    pi.political_status = "party_member"
    pi.birth_date = "2002-10"
    # to_dict 应包含新字段
    d = pi.to_dict()
    assert d["political_status"] == "party_member"
    assert d["birth_date"] == "2002-10"
