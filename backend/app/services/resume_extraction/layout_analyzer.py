"""
版面分析器
自动识别简历的章节结构和条目边界
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from .models import (
    ParsedDocument, DocumentStructure, Section, SectionType,
    TextBlock, EducationEntry, WorkEntry, ProjectEntry
)
from .config import layout_config
from .utils import extract_date_range, clean_text

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """简历版面分析器"""
    
    def __init__(self):
        self.config = layout_config
        self.section_patterns = self._build_section_patterns()
    
    def analyze(self, document: ParsedDocument) -> DocumentStructure:
        """
        分析文档结构
        
        Args:
            document: 解析后的文档
            
        Returns:
            DocumentStructure: 文档结构（章节、段落等）
        """
        logger.info("开始版面分析...")
        
        # 识别章节
        sections = self._detect_sections(document.raw_text)
        
        # 验证并修正章节分类
        sections = self._validate_and_fix_sections(sections)
        
        # 为每个章节提取条目
        for section in sections:
            section.entries = self._extract_entries(section)
        
        structure = DocumentStructure(
            sections=sections,
            text_blocks=document.text_blocks,
            image_blocks=document.image_blocks
        )
        
        logger.info(f"版面分析完成，识别到 {len(sections)} 个章节")
        return structure
    
    def _build_section_patterns(self) -> Dict[SectionType, List[re.Pattern]]:
        """构建章节识别模式"""
        patterns = {}
        
        for section_type, keywords in self.config.section_keywords.items():
            section_enum = SectionType(section_type)
            patterns[section_enum] = []
            
            for keyword in keywords:
                # 构建多种匹配模式
                # 模式1: 关键词在行首，可能后跟分隔符
                pattern1 = rf'^[\s]*{re.escape(keyword)}[\s]*[:：\-]*[\s]*$'
                # 模式2: 关键词作为独立标题
                pattern2 = rf'\b{re.escape(keyword)}\b'
                
                patterns[section_enum].append(re.compile(pattern1, re.MULTILINE | re.IGNORECASE))
                patterns[section_enum].append(re.compile(pattern2, re.MULTILINE | re.IGNORECASE))
        
        return patterns
    
    def _detect_sections(self, text: str) -> List[Section]:
        """检测文档章节 - 增强版本，支持极简格式"""
        sections = []
        lines = text.split('\n')
        
        # 查找所有可能的章节标题位置
        section_positions = []
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 检查是否匹配任何章节模式
            for section_type, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if pattern.search(line_stripped):
                        # 验证这确实是一个章节标题（不是正文内容）
                        if self._is_valid_section_header(line_stripped, section_type):
                            section_positions.append({
                                "line_num": line_num,
                                "title": line_stripped,
                                "type": section_type
                            })
                            break
        
        # 按行号排序
        section_positions.sort(key=lambda x: x["line_num"])
        
        # 合并相邻的相同类型章节（去重）
        section_positions = self._deduplicate_sections(section_positions)
        
        # 创建Section对象
        for i, pos in enumerate(section_positions):
            start_line = pos["line_num"] + 1  # 章节内容从标题下一行开始
            
            # 确定章节结束位置
            if i < len(section_positions) - 1:
                end_line = section_positions[i + 1]["line_num"]
            else:
                end_line = len(lines)
            
            # 提取章节内容
            content_lines = lines[start_line:end_line]
            content = '\n'.join(content_lines).strip()
            
            section = Section(
                section_type=pos["type"],
                title=pos["title"],
                content=content,
                start_line=start_line,
                end_line=end_line,
                confidence=0.9
            )
            sections.append(section)
        
        # 如果没有识别到章节，先尝试宽松的 fallback 章节识别，再走极简格式
        if not sections:
            sections = self._fallback_section_detection(text)
            if not sections:
                sections = self._parse_minimal_format(lines)

        return sections
    
    def _parse_minimal_format(self, lines: List[str]) -> List[Section]:
        """解析极简格式简历（无明确章节标题）"""
        sections = []
        
        # 极简格式通常按顺序包含：个人信息、教育、工作、技能
        # 我们根据内容特征来推断
        
        current_section = None
        current_content = []
        current_start = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 尝试识别内容类型
            content_type = self._infer_content_type(line_stripped, i, lines)
            
            if content_type:
                # 如果类型变化，保存当前章节
                if current_section and current_section != content_type and current_content:
                    section = Section(
                        section_type=current_section,
                        title=self._get_section_title(current_section),
                        content='\n'.join(current_content).strip(),
                        start_line=current_start,
                        end_line=i,
                        confidence=0.6
                    )
                    sections.append(section)
                    current_content = []
                
                if not current_content:
                    current_start = i
                    current_section = content_type
                
                current_content.append(line_stripped)
        
        # 保存最后一个章节
        if current_section and current_content:
            section = Section(
                section_type=current_section,
                title=self._get_section_title(current_section),
                content='\n'.join(current_content).strip(),
                start_line=current_start,
                end_line=len(lines),
                confidence=0.6
            )
            sections.append(section)
        
        return sections
    
    def _infer_content_type(self, line: str, line_num: int, all_lines: List[str]) -> Optional[SectionType]:
        """推断内容类型 - 增强版本，解决教育/工作特征重叠问题"""
        
        # 定义特征关键词
        education_keywords = ['大学', '学院', '学校', 'University', 'College', '本科', '硕士', '博士', 'Bachelor', 'Master', 'PhD']
        work_keywords = ['公司', '集团', 'Corp', 'Inc', 'Ltd', '工程师', '经理', '主管', '总监']
        # "科技"和"网络"可能同时出现在学校名和公司名中，作为弱特征
        weak_work_keywords = ['科技', '网络', '软件']
        
        has_education = any(kw in line for kw in education_keywords)
        has_work = any(kw in line for kw in work_keywords)
        has_weak_work = any(kw in line for kw in weak_work_keywords)
        
        # 决策逻辑：教育特征优先于工作特征
        # 当一行同时包含教育和工作特征时，优先判定为教育经历
        # 这是因为：学校名称（如"北京科技大学"）包含"科技"，但本质上是教育经历
        if has_education:
            # 检查是否是纯学校名称（如"北京科技大学"）
            # 纯学校名称通常较短（<15字符）且包含"大学/学院/学校"
            if len(line.strip()) < 20:
                return SectionType.EDUCATION
            # 如果同时包含强工作特征（如"公司"），需要进一步判断
            if has_work:
                # 如果包含"公司"等强工作特征，判定为工作
                if any(kw in line for kw in ['公司', '集团', 'Corp', 'Inc', 'Ltd']):
                    return SectionType.WORK_EXPERIENCE
            # 否则优先教育
            return SectionType.EDUCATION
        
        # 只有工作特征（无教育特征）
        if has_work or has_weak_work:
            return SectionType.WORK_EXPERIENCE
        
        # 技能特征
        if re.search(r'(Python|Java|SQL|MySQL|Redis|Docker|Kubernetes|Photoshop|Excel|Word|OpenClaw|ClaudeCode|MATLAB|Tableau|ArcGIS)', line, re.IGNORECASE):
            return SectionType.SKILLS
        
        # 项目经历特征
        if re.search(r'(项目|课题|Project|负责|开发)', line, re.IGNORECASE) and len(line) < 50:
            return SectionType.PROJECTS
        
        # 时间范围特征（可能是教育或工作）
        if re.search(r'20\d{2}[\.\-/年]', line):
            # 根据上下文判断
            if line_num > 0:
                prev_line = all_lines[line_num - 1].strip()
                if re.search(r'(大学|学院|学校)', prev_line):
                    return SectionType.EDUCATION
                elif re.search(r'(公司|集团)', prev_line):
                    return SectionType.WORK_EXPERIENCE
        
        return None
    
    def _get_section_title(self, section_type: SectionType) -> str:
        """获取章节标题"""
        titles = {
            SectionType.EDUCATION: "教育背景",
            SectionType.WORK_EXPERIENCE: "工作经历",
            SectionType.PROJECTS: "项目经历",
            SectionType.SKILLS: "技能",
            SectionType.CERTIFICATIONS: "证书",
            SectionType.LANGUAGES: "语言能力",
            SectionType.AWARDS: "奖项荣誉",
            SectionType.SELF_EVALUATION: "自我评价",
        }
        return titles.get(section_type, "其他")
    
    def _is_valid_section_header(self, line: str, section_type: SectionType) -> bool:
        """
        验证是否为有效的章节标题 — P0-4 加固版
        - 放宽长度限制（带空格标题可能较长）
        - 允许带"·"或全角分隔符
        - 教育章节明确允许"教育/学历"关键词
        """
        line_stripped = line.strip()

        if not line_stripped:
            return False

        # 1. 长度检查：放宽到 80 字符
        if len(line_stripped) > 80:
            return False

        # 2. 去空格（含全角空格）后检查长度：2-25 字符
        line_no_space = line_stripped.replace(' ', '').replace('\u3000', '')
        if len(line_no_space) < 2 or len(line_no_space) > 25:
            return False

        # 3. 排除明显的非标题特征
        excluded_patterns = [
            r'\d{4}[\.\-/年]',  # 日期
            r'@',  # 邮箱
            r'1[3-9]\d{9}',  # 手机号
            r'http[s]?://',  # URL
        ]
        for pattern in excluded_patterns:
            if re.search(pattern, line_stripped):
                return False

        # 4. ★ P0-4 教育章节：放行带教育/学历关键词的标题
        if section_type == SectionType.EDUCATION:
            # 含"教育/学历/Education/Academic"等关键词 → 放行（覆盖原"校名拦截"逻辑）
            edu_header_keywords = ['教育', '学历', 'Education', 'Academic', '学习']
            if any(kw in line_no_space for kw in edu_header_keywords):
                return True  # ★ 优先放行
            # 纯校名（如"北京大学"）不应作为章节标题
            school_keywords = ['大学', '学院', '学校', 'University', 'College']
            if any(line_no_space.endswith(kw) for kw in school_keywords) and len(line_no_space) <= 10:
                return False

        # 5. 工作章节不应包含公司名（但允许"工作/职业"关键词）
        if section_type == SectionType.WORK_EXPERIENCE:
            work_header_keywords = ['工作', '职业', '实习', 'Experience', 'Work', 'Career']
            if any(kw in line_no_space for kw in work_header_keywords):
                return True
            company_keywords = ['公司', '集团', 'Corp', 'Inc', 'Ltd', '科技', '网络']
            if any(kw in line_no_space for kw in company_keywords) and len(line_no_space) > 8:
                return False

        # 6. 项目章节
        if section_type == SectionType.PROJECTS:
            project_header_keywords = ['项目', 'Project', '课题', '研究']
            if any(kw in line_no_space for kw in project_header_keywords):
                return True
            project_indicators = ['项目：', '课题：', '《', '》', '负责', '开发']
            if any(ind in line_stripped for ind in project_indicators):
                return False

        # 7. 标点检查：允许"·"或"-"分隔（"教·育·背·景"）
        # 拦截明显的段落标点
        if re.search(r'[。，、；：！？]', line_stripped):
            return False
        # 允许 "·" "—" "-" 不在拦截列表

        return True

    def _fallback_section_detection(self, text: str) -> List[Section]:
        """
        P0-4 新增：无标题简历的 fallback 章节识别
        当章节识别失败时（如纯文本简历无标题），根据内容特征推断章节
        """
        sections = []
        lines = text.split('\n')
        current_section: Optional[Section] = None
        current_content: List[str] = []

        # 宽松的章节标题模式（带可选空格/标点/中英混合）
        section_patterns = [
            (r'(?:^|\s)教\s*育\s*(?:背\s*景|经\s*历|情\s*况)|^Education\b|^EDUCATION', SectionType.EDUCATION, "教育背景"),
            (r'(?:^|\s)工\s*作\s*(?:经\s*历|经\s*验)|^Experience\b|^EXPERIENCE|^Work\s+Experience', SectionType.WORK_EXPERIENCE, "工作经历"),
            (r'(?:^|\s)项\s*目\s*(?:经\s*历|经\s*验)|^Project\b|^PROJECT', SectionType.PROJECTS, "项目经历"),
            (r'(?:^|\s)实\s*习|^Internship\b|^INTERNSHIP', SectionType.WORK_EXPERIENCE, "实习经历"),
            (r'(?:^|\s)(?:专\s*业\s*)?技\s*能|^Skill\b|^SKILL', SectionType.SKILLS, "技能"),
            (r'(?:^|\s)(?:获\s*得\s*)?证\s*书|^Certification', SectionType.CERTIFICATIONS, "证书"),
            (r'(?:^|\s)荣\s*誉|^Award\b|^AWARD', SectionType.AWARDS, "荣誉奖项"),
            (r'(?:^|\s)自\s*我\s*评\s*价|^Summary|^SUMMARY', SectionType.SELF_EVALUATION, "自我评价"),
            (r'(?:^|\s)语\s*言|^Language', SectionType.LANGUAGES, "语言能力"),
        ]

        def _flush_current():
            nonlocal current_section, current_content
            if current_section and current_content:
                current_section.content = '\n'.join(current_content).strip()
                if current_section.content:
                    sections.append(current_section)
            current_section = None
            current_content = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            matched = False
            for pattern, section_type, default_title in section_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    _flush_current()
                    current_section = Section(
                        title=default_title,
                        section_type=section_type,
                        content="",
                        start_line=0,
                        end_line=0,
                        confidence=0.6,  # fallback 置信度低
                    )
                    matched = True
                    break
            if not matched and current_section:
                current_content.append(line_stripped)

        _flush_current()
        return sections
    
    def _deduplicate_sections(self, positions: List[Dict]) -> List[Dict]:
        """去重相邻的相同类型章节"""
        if not positions:
            return positions
        
        deduplicated = [positions[0]]
        
        for pos in positions[1:]:
            last = deduplicated[-1]
            # 如果类型相同且距离很近，认为是重复
            if pos["type"] == last["type"] and pos["line_num"] - last["line_num"] <= 2:
                continue
            deduplicated.append(pos)
        
        return deduplicated
    
    def _validate_and_fix_sections(self, sections: List[Section]) -> List[Section]:
        """验证并修正章节分类 - 新增方法"""
        if not sections:
            return sections
        
        validated_sections = []
        
        for section in sections:
            # 验证章节内容是否符合类型特征
            is_valid, suggested_type = self._validate_section_content(section)
            
            if is_valid:
                validated_sections.append(section)
            elif suggested_type:
                # 修正章节类型
                logger.warning(f"章节'{section.title}'从{section.section_type.value}修正为{suggested_type.value}")
                section.section_type = suggested_type
                validated_sections.append(section)
            else:
                # 无法确定类型，保留原样但降低置信度
                section.confidence = 0.5
                validated_sections.append(section)
        
        return validated_sections
    
    def _validate_section_content(self, section: Section) -> Tuple[bool, Optional[SectionType]]:
        """验证章节内容是否符合其声明的类型"""
        content = section.content
        section_type = section.section_type
        
        # 教育经历验证 - 应包含学校名称
        if section_type == SectionType.EDUCATION:
            school_keywords = ['大学', '学院', '学校', 'University', 'College', 'Institute']
            has_school = any(kw in content for kw in school_keywords)
            degree_keywords = ['本科', '硕士', '博士', '学士', 'Bachelor', 'Master', 'PhD']
            has_degree = any(kw in content for kw in degree_keywords)
            
            if has_school or has_degree:
                return True, None
            else:
                # 可能是工作经历误入
                company_keywords = ['公司', '集团', 'Corp', 'Inc', 'Ltd']
                if any(kw in content for kw in company_keywords):
                    return False, SectionType.WORK_EXPERIENCE
                return False, None
        
        # 工作经历验证 - 应包含公司或职位信息
        if section_type == SectionType.WORK_EXPERIENCE:
            company_keywords = ['公司', '集团', 'Corp', 'Inc', 'Ltd', '科技', '网络']
            title_keywords = ['工程师', '经理', '主管', '总监', '开发', 'Engineer', 'Manager']

            has_company = any(kw in content for kw in company_keywords)
            has_title = any(kw in content for kw in title_keywords)
            has_date = re.search(r'20\d{2}[\.\-/年]', content) is not None

            # ★ P0-4 修复：日期+学校同时出现 → 修正为教育
            school_keywords = ['大学', '学院', '学校', 'University', 'College']
            degree_keywords = ['本科', '硕士', '博士', 'Bachelor', 'Master', 'PhD', '研究生']
            school_count = sum(1 for kw in school_keywords if kw in content)
            degree_count = sum(1 for kw in degree_keywords if kw in content)
            if school_count >= 1 and (has_date or degree_count >= 1):
                return False, SectionType.EDUCATION  # ★ 修正为教育

            if has_company or has_title:
                # 原有逻辑：school_count >= 2 修正为教育
                if school_count >= 2:
                    return False, SectionType.EDUCATION
                return True, None
            else:
                # 可能是其他类型
                return False, None
        
        # 项目经历验证
        if section_type == SectionType.PROJECTS:
            project_keywords = ['项目', '课题', 'Project', '负责', '开发', '设计', '实现']
            has_project = any(kw in content for kw in project_keywords)
            
            if has_project:
                return True, None
            return False, None
        
        return True, None
    
    def _extract_entries(self, section: Section) -> List[Dict]:
        """从章节内容中提取条目"""
        if section.section_type == SectionType.EDUCATION:
            return self._extract_education_entries(section.content)
        elif section.section_type == SectionType.WORK_EXPERIENCE:
            return self._extract_work_entries(section.content)
        elif section.section_type == SectionType.PROJECTS:
            return self._extract_project_entries(section.content)
        elif section.section_type == SectionType.SKILLS:
            return self._extract_skill_entries(section.content)
        else:
            return []
    
    def _extract_education_entries(self, content: str) -> List[Dict]:
        """提取教育经历条目"""
        entries = []
        paragraphs = self._split_into_paragraphs(content)
        
        for para in paragraphs:
            entry = self._parse_education_paragraph(para)
            if entry and entry.get("school"):
                entries.append(entry)
        
        return entries
    
    def _extract_work_entries(self, content: str) -> List[Dict]:
        """提取工作经历条目"""
        entries = []
        paragraphs = self._split_into_paragraphs(content)
        
        for para in paragraphs:
            entry = self._parse_work_paragraph(para)
            if entry and entry.get("company"):
                entries.append(entry)
        
        return entries
    
    def _extract_project_entries(self, content: str) -> List[Dict]:
        """提取项目经历条目 - 改进版本，支持项目聚类"""
        entries = []
        paragraphs = self._split_into_paragraphs(content)
        
        # 首先解析所有段落
        parsed_entries = []
        for para in paragraphs:
            entry = self._parse_project_paragraph(para)
            if entry and entry.get("name"):
                parsed_entries.append(entry)
        
        # 使用聚类算法合并相关的项目条目
        merged_entries = self._merge_related_projects(parsed_entries)
        
        return merged_entries
    
    def _merge_related_projects(self, entries: List[Dict]) -> List[Dict]:
        """合并相关的项目条目 - 防止过度拆分"""
        if len(entries) <= 1:
            return entries
        
        merged = []
        i = 0
        while i < len(entries):
            current = entries[i]
            
            # 检查后续条目是否应该合并
            j = i + 1
            while j < len(entries):
                next_entry = entries[j]
                
                # 判断是否属于同一项目
                if self._should_merge_projects(current, next_entry):
                    # 合并描述
                    current["description"] = current.get("description", "") + "\n" + next_entry.get("description", "")
                    # 合并技术栈
                    current["technologies"] = list(set(
                        current.get("technologies", []) + next_entry.get("technologies", [])
                    ))
                    j += 1
                else:
                    break
            
            merged.append(current)
            i = j if j > i + 1 else i + 1
        
        return merged
    
    def _should_merge_projects(self, entry1: Dict, entry2: Dict) -> bool:
        """判断两个项目条目是否应该合并"""
        name1 = entry1.get("name", "")
        name2 = entry2.get("name", "")
        
        # 如果名称相同或非常相似，合并
        if name1 and name2:
            # 完全匹配
            if name1 == name2:
                return True
            
            # 一个包含另一个
            if name1 in name2 or name2 in name1:
                return True
            
            # 相似度检查（简单版本）
            similarity = self._calculate_name_similarity(name1, name2)
            if similarity > 0.7:
                return True
        
        # 检查时间连续性
        time1 = entry1.get("start_date", "")
        time2 = entry2.get("start_date", "")
        if time1 and time2 and time1 == time2:
            return True
        
        # 检查描述相关性
        desc1 = entry1.get("description", "")
        desc2 = entry2.get("description", "")
        if desc1 and desc2:
            # 如果描述都很短，可能是同一项目的不同方面
            if len(desc1) < 50 and len(desc2) < 50:
                return True
        
        return False
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算两个项目名称的相似度"""
        # 简单的Jaccard相似度
        set1 = set(name1.lower())
        set2 = set(name2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_skill_entries(self, content: str) -> List[Dict]:
        """提取技能条目"""
        # 技能通常是列表形式，用分隔符分隔
        skills = []
        
        # 尝试多种分隔符
        for separator in [',', '，', ';', '；', '、', '|', '/']:
            if separator in content:
                items = content.split(separator)
                for item in items:
                    item = item.strip()
                    if item and len(item) < 50:  # 技能名称通常较短
                        skills.append({"name": item})
                break
        
        # 如果没有找到分隔符，尝试按行分割
        if not skills:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # 移除列表符号
                line = re.sub(r'^[•\-\*・]', '', line).strip()
                if line and len(line) < 50:
                    skills.append({"name": line})
        
        return skills
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """将文本分割成段落（条目）"""
        # 策略1: 按空行分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 策略2: 按时间模式分割
        if len(paragraphs) <= 1:
            # 尝试按日期开头分割
            paragraphs = re.split(r'(?=20\d{2}[\.\-/年])', text)
        
        # 策略3: 按列表符号分割
        if len(paragraphs) <= 1:
            paragraphs = re.split(r'(?=[•\-\*・])', text)
        
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _parse_education_paragraph(self, text: str) -> Dict:
        """解析教育经历段落"""
        entry = {
            "school": "",
            "degree": "",
            "field": "",
            "start_date": "",
            "end_date": ""
        }
        
        lines = text.split('\n')
        full_text = text
        
        # 提取学校名称
        school_patterns = [
            r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))',
            r'([\u4e00-\u9fa5]{2,20}(?:University|College|Institute|School)[^\n,]*?)',
        ]
        
        for pattern in school_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                school = match.group(1).strip()
                if len(school) > 2 and len(school) < 60:
                    entry["school"] = school
                    break
        
        # 提取学位
        degree_map = {
            "博士": ["博士", "PhD", "Ph.D", "Doctor", "Doctorate"],
            "硕士": ["硕士", "Master", "MBA", "EMBA", "硕士研究生"],
            "本科": ["本科", "学士", "Bachelor", "Undergraduate"],
            "专科": ["专科", "大专", "Associate"]
        }
        
        for degree_name, keywords in degree_map.items():
            for keyword in keywords:
                if keyword in full_text:
                    entry["degree"] = degree_name
                    break
            if entry["degree"]:
                break
        
        # 提取专业
        field_patterns = [
            r'(?:专业|Major|Field)[:：\s]*([\u4e00-\u9fa5]{2,15})',
            r'(?:学士|硕士|博士)\s*(?:学位)?[:：\s]*([\u4e00-\u9fa5]{2,15})',
            r'([\u4e00-\u9fa5]{2,10}(?:学|工程|技术|科学|管理))',
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                field = match.group(1).strip()
                if len(field) > 1 and len(field) < 30 and field not in ["专业", "学位"]:
                    entry["field"] = field
                    break
        
        # 提取时间
        start_date, end_date = extract_date_range(full_text)
        entry["start_date"] = start_date
        entry["end_date"] = end_date
        
        return entry
    
    def _parse_work_paragraph(self, text: str) -> Dict:
        """解析工作经历段落"""
        entry = {
            "company": "",
            "title": "",
            "start_date": "",
            "end_date": "",
            "description": ""
        }
        
        lines = text.split('\n')
        full_text = text
        
        # 提取公司名称
        company_patterns = [
            r'([^\n]*(?:公司|集团|科技|网络|软件|互联网|Corp|Inc|Ltd|LLC)[^\n,]*)',
            r'(?:公司|单位|组织)[:\s]*([^\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                company = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                company = re.sub(r'^(?:公司|单位)[:\s]*', '', company, flags=re.IGNORECASE)
                if len(company) > 2 and len(company) < 80:
                    entry["company"] = company
                    break
        
        # 提取职位
        title_patterns = [
            r'(?:职位|岗位|职务|Title)[:\s]*([^\n]+)',
            r'((?:高级|资深|初级|助理)?\s*[^\n]{2,20}(?:工程师|开发|经理|主管|总监|架构师|负责人))',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                title = re.sub(r'^(?:职位|岗位|职务)[:\s]*', '', title, flags=re.IGNORECASE)
                if len(title) > 1 and len(title) < 50:
                    entry["title"] = title
                    break
        
        # 提取时间
        start_date, end_date = extract_date_range(full_text)
        entry["start_date"] = start_date
        entry["end_date"] = end_date
        
        # 剩余内容作为描述
        entry["description"] = full_text
        
        return entry
    
    def _parse_project_paragraph(self, text: str) -> Dict:
        """解析项目经历段落"""
        entry = {
            "name": "",
            "role": "",
            "start_date": "",
            "end_date": "",
            "description": ""
        }
        
        lines = text.split('\n')
        
        # 第一行通常是项目名称
        if lines:
            first_line = lines[0].strip()
            # 移除列表符号
            first_line = re.sub(r'^[•\-\*・《]', '', first_line).strip()
            if first_line and len(first_line) < 100:
                entry["name"] = first_line
        
        # 提取角色
        role_patterns = [
            r'(?:角色|职责|Role|Position)[:\s]*([^\n]+)',
            r'((?:负责|担任|作为)[^\n]{2,20}(?:开发|工程师|负责人|架构师))',
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                role = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                if len(role) > 1 and len(role) < 50:
                    entry["role"] = role
                    break
        
        # 提取时间
        start_date, end_date = extract_date_range(text)
        entry["start_date"] = start_date
        entry["end_date"] = end_date
        
        # 剩余内容作为描述
        entry["description"] = text
        
        return entry


# 单例模式
_layout_analyzer = None

def get_layout_analyzer() -> LayoutAnalyzer:
    """获取版面分析器单例"""
    global _layout_analyzer
    if _layout_analyzer is None:
        _layout_analyzer = LayoutAnalyzer()
    return _layout_analyzer
