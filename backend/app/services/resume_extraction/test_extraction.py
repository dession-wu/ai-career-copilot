"""
简历信息提取测试脚本
用于测试和验证提取效果
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from .extraction_engine import extract_resume_from_text
from .models import ResumeData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 测试用例 - 截图中的简历文本
TEST_RESUME_TEXT = """吴烨
中共党员丨2002.10丨安徽安庆
18133004892丨18133004892@163.com

教 育 背 景
2024.09-至今 浙江大学 环境科学（硕士）
2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）
2022.08-2023.01 华南理工大学（4.0/4.0） 环境工程（交流）
专业学习：本科期间，排名5％，保送至浙江大学攻读硕士学位。
英语水平：CET4-602（阅读213）、CET6-557（阅读222）、参与全英夏令营且结营成绩优异。

项 目 经 历
2023.07-2024.01 中国建设科技集团 《北京市生活垃圾管理全过程碳排放测算服务》
本项目承接自北京市城市管理委员会，主要针对北京市2015年至2035年期间生活垃圾管理全过程的碳排放做出量化。
报告输出：将垃圾分类后的情景与分类前的情景进行定量对比，识别温室气体排放关键点，为北京市生活垃圾管理发展趋势提出低碳减排建议，输出方案设计书、服务报告等。
模型构建：协助完成碳核算模型构建与运行，完成居民生活垃圾碳账户测算体系搭建，Python处理数据10万余条。

2023.03-2023.07 综合课题训练 《1980-2060年中国水泥行业碳排放与碳汇核算》
本项目主要研究1980-2020年水泥行业的碳排放并对未来不同减排情景进行拟合预测，探究水泥碳汇在碳减排领域的潜力。
数据分析：在项目中查阅相关文献，开展1980-1990年中国水泥行业相关数据挖掘与分析，同时利用MATLAB、Origin、Pandas等工具，完成1980-2020年中国水泥行业碳排放与碳汇2000多项相关数据的计算。

2022.11-2024.07 北京市大学生创新创业项目 《金属废渣湿法回收及发酵液低碳处理系统》
本项目主要针对金属废渣的低碳处理，尝试建立利用厨余垃圾发酵酸处理金属废渣的完善系统。
创新思维：作为项目负责人，基于团队前期研究，提出了将金属废渣转化为铁氧软磁体的处理思路，设计了分离富集含重金属有机溶液的电渗析装置，显著提高处理效果，同时实现金属资源的高效利用。
项目成果：项目获校级一等奖两项、北京市"挑战杯"专项赛三等奖、北京市节能节水科技竞赛三等奖。

2021.10-2022.08 全国大学生节能减排科技竞赛 《基于有机发酵酸浸取废旧干电池的资源化处理装置》
本项目主要针对废旧干电池污染及金属资源浪费等问题，旨在探寻可持续资源化新方式。
跟进管理：作为项目负责人，创新性地提出利用厨余垃圾发酵酸代替工业酸进行溶浸的策略，同时设计实验进行验证，并参与实物装置的搭建制作。
项目成果：项目获第十五届全国大学生节能减排社会实践与科技竞赛一等奖，一项实用新型专利（第一发明人）已授权，一项国家发明专利（学生第一发明人）已授权（目前已成功转让）。

工 作 实 践
2023.07-2024.01 中国建设科技集团 助理研究员
实习期间，全程参与北京市城市管理委员会《北京市生活垃圾管理全过程碳排放测算服务》项目（24万）。

2022.05-2024.07 "烨金科技"初创团队 负责人
创业期间，斩获多项创新创业竞赛奖项，入驻现代汽车、中国青年创业就业基金会孵化平台，获数万资金支持。

2021.12-2024.07 能源与环境工程学院团委学业发展中心 部长、负责人
在任期间，对接安排朋辈习题课 50 余节，组织举办特种奖学金答辩等活动 30 余场，连续两年获评"优秀部门"。

2020.09-2024.07 能源2006班、环境202班 班长

奖 项 荣 誉
奖项荣誉：优秀三好学生、优秀学生干部、标兵宿舍长（两次）、国家励志奖学金（两次）、人民奖学金（两次）等。
竞赛获奖：国家级（1项）、省部级（5项）：全国大学生节能减排社会实践与科技竞赛一等奖（负责人）、中国国际"互联网+"大赛北京赛区三等奖、"挑战杯"科技竞赛市级三等奖（负责人）、节能节水低碳减排科技竞赛三等奖（负责人）；校级（7项）：节能减排社会实践与科技竞赛一等奖（负责人）、 "摇篮杯"科技竞赛一等奖（负责人）等。

其 他 信 息
专业技能：MATLAB建模、Python数据处理、MySQL、R语言、Tableau可视化、Microsoft Office、PS/PR、ArcGIS等。
个人主页：https://blog.csdn.net/dession_Wu（CSDN）
"""


def test_extraction():
    """测试简历提取"""
    print("=" * 60)
    print("简历信息提取测试")
    print("=" * 60)
    
    # 执行提取
    print("\n开始提取...")
    resume_data = extract_resume_from_text(TEST_RESUME_TEXT)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("提取结果")
    print("=" * 60)
    
    # 个人信息
    print("\n【个人信息】")
    print(f"  姓名: {resume_data.personal_info.name}")
    print(f"  邮箱: {resume_data.personal_info.email}")
    print(f"  电话: {resume_data.personal_info.phone}")
    print(f"  置信度: {resume_data.personal_info.confidence}")
    
    # 教育经历
    print("\n【教育经历】")
    for i, edu in enumerate(resume_data.education, 1):
        print(f"  {i}. {edu.school} - {edu.degree}")
        print(f"     专业: {edu.field}")
        print(f"     时间: {edu.start_date} - {edu.end_date}")
        print(f"     置信度: {edu.confidence}")
    
    # 工作经历
    print("\n【工作经历】")
    for i, work in enumerate(resume_data.work_experience, 1):
        print(f"  {i}. {work.company} - {work.title}")
        print(f"     时间: {work.start_date} - {work.end_date}")
        print(f"     置信度: {work.confidence}")
    
    # 项目经历
    print("\n【项目经历】")
    for i, proj in enumerate(resume_data.projects, 1):
        print(f"  {i}. {proj.name}")
        print(f"     角色: {proj.role}")
        print(f"     时间: {proj.start_date} - {proj.end_date}")
        print(f"     置信度: {proj.confidence}")
    
    # 技能
    print("\n【技能】")
    print(f"  共识别 {len(resume_data.skills)} 个技能:")
    for skill in resume_data.skills:
        print(f"    - {skill.name} ({skill.level}) [{skill.category}] 置信度:{skill.confidence}")
    
    # 质量报告
    print("\n" + "=" * 60)
    print("质量报告")
    print("=" * 60)
    print(f"整体分数: {resume_data.metadata.confidence_score:.2f}")
    print(f"完整度: {resume_data.metadata.completeness_score:.2f}")
    print(f"提取耗时: {resume_data.metadata.extraction_time_ms}ms")
    print(f"PDF类型: {resume_data.metadata.pdf_type.value}")
    
    # 保存结果
    output_path = Path("test_extraction_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resume_data.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_path}")
    
    return resume_data


def test_skill_extraction():
    """专门测试技能提取"""
    print("\n" + "=" * 60)
    print("技能提取专项测试")
    print("=" * 60)
    
    # 测试文本中包含的技能
    test_text = """
    专业技能：MATLAB建模、Python数据处理、MySQL、R语言、Tableau可视化、Microsoft Office、PS/PR、ArcGIS等。
    技术栈：Java, Spring Boot, React, Vue.js, Node.js, Docker, Kubernetes
    编程语言：Python, Java, C++, JavaScript, TypeScript
    数据库：MySQL, PostgreSQL, MongoDB, Redis
    工具：Git, Jenkins, Jira, Confluence
    """
    
    resume_data = extract_resume_from_text(test_text)
    
    print(f"\n识别到 {len(resume_data.skills)} 个技能:")
    for skill in resume_data.skills:
        print(f"  - {skill.name} ({skill.level}) [{skill.category}]")
    
    # 验证关键技能
    expected_skills = ["MATLAB", "Python", "MySQL", "R语言", "Tableau"]
    found_skills = [s.name.lower() for s in resume_data.skills]
    
    print("\n关键技能检查:")
    for skill in expected_skills:
        found = any(skill.lower() in fs for fs in found_skills)
        status = "✓" if found else "✗"
        print(f"  {status} {skill}")


if __name__ == "__main__":
    # 运行测试
    test_extraction()
    test_skill_extraction()
