import os
import uuid
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models.career_vault import CareerVault
from app.schemas.vault import CareerVaultCreate, CareerVaultUpdate
from app.config import get_settings

# 导入新的简历提取服务
from app.services.resume_extraction import ResumeExtractionService

settings = get_settings()
logger = logging.getLogger(__name__)


class VaultService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = settings.UPLOAD_DIR
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """从 PDF 文件提取文本"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            extracted_text = text.strip()
            logger.info(f"PDF text extraction complete, length: {len(extracted_text)} chars")
            return extracted_text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF 解析失败: {str(e)}"
            )

    def _extract_text_from_docx(self, file_path: str) -> str:
        """从 Word 文件提取文本"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            extracted_text = text.strip()
            logger.info(f"Word document text extraction complete, length: {len(extracted_text)} chars")
            return extracted_text
        except Exception as e:
            logger.error(f"Word document text extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Word 文档解析失败: {str(e)}"
            )

    def parse_resume_file(self, file: UploadFile) -> str:
        """
        解析简历文件，提取原始文本
        支持 PDF 和 Word 格式
        """
        logger.info(f"Received file upload: {file.filename}, content_type: {file.content_type}")

        # 检查文件类型
        allowed_types = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
        }

        content_type = file.content_type or ''

        # 如果没有 content_type，尝试从文件名推断
        if not content_type and file.filename:
            if file.filename.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif file.filename.lower().endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file.filename.lower().endswith('.doc'):
                content_type = 'application/msword'

        if content_type not in allowed_types:
            logger.warning(f"Unsupported file type: {content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {content_type or '未知'}。请上传 PDF 或 Word 文档。"
            )

        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头

        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件过大，最大支持 {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        logger.info(f"File validation passed: {file.filename}, size: {file_size} bytes")

        # 保存文件到临时目录
        file_ext = allowed_types[content_type]
        temp_filename = f"{uuid.uuid4()}.{file_ext}"
        temp_path = os.path.join(self.upload_dir, temp_filename)

        try:
            with open(temp_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)

            logger.info(f"File saved to temp location: {temp_path}")

            # 根据文件类型提取文本
            if file_ext == 'pdf':
                text = self._extract_text_from_pdf(temp_path)
            elif file_ext in ['docx', 'doc']:
                text = self._extract_text_from_docx(temp_path)
            else:
                text = ""

            return text

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"Temp file cleaned up: {temp_path}")

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """提取教育经历 - 增强版，支持多行解析和多种格式"""
        education_list = []

        # 教育相关关键词
        edu_keywords = ['教育背景', '教育经历', '学历', 'Education', 'Academic', 'EDUCATION']
        school_keywords = ['大学', '学院', '学校', 'University', 'College', 'Institute', 'Academy', 'School']
        degree_keywords = ['博士', '硕士', '学士', '本科', '专科', 'MBA', 'PhD', 'Ph.D', 'Master', 'Bachelor',
                          'Doctor', 'Undergraduate', '研究生', '本科生', '大专']

        # 查找教育背景部分
        edu_section = self._find_section(text, edu_keywords)
        if not edu_section:
            # 如果没有明确分区，尝试全文搜索
            edu_section = text

        # 解析教育条目 - 使用多种分隔模式
        # 模式1: 学校名作为条目开始
        # 模式2: 时间作为条目开始
        # 模式3: 学位作为条目开始

        entries = self._split_into_entries(edu_section, school_keywords)

        for entry in entries[:10]:  # 最多处理10个条目
            edu_item = self._parse_education_entry(entry)
            if edu_item and edu_item.get('school'):
                education_list.append(edu_item)

        logger.info(f"Extracted {len(education_list)} education entries")
        return education_list[:5]

    def _find_section(self, text: str, section_keywords: List[str]) -> Optional[str]:
        """查找特定部分的内容"""
        lines = text.split('\n')
        section_start = -1
        section_end = len(lines)

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # 检查是否是章节标题
            for keyword in section_keywords:
                if keyword in line_stripped:
                    # 确保这看起来像一个标题（短行或带分隔符）
                    if len(line_stripped) < 30 or any(sep in line_stripped for sep in ['=', '-', ':', '：']):
                        section_start = i + 1
                        break
            if section_start >= 0:
                break

        if section_start < 0:
            return None

        # 查找章节结束（下一个章节开始）
        other_section_patterns = [
            r'^(?:工作经验|工作经历|Work Experience|EXPERIENCE|项目经历|技能|SKILLS|个人简介|自我评价)',
            r'^[\u4e00-\u9fa5]{2,8}[:：]\s*$',
            r'^[A-Z\s]{3,20}[:：]\s*$'
        ]

        for i in range(section_start, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            for pattern in other_section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    section_end = i
                    break
            if section_end < len(lines):
                break

        return '\n'.join(lines[section_start:section_end])

    def _split_into_entries(self, text: str, start_keywords: List[str]) -> List[str]:
        """将文本分割成条目列表"""
        if not text:
            return []

        entries = []
        current_entry = []

        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # 检查是否是新条目的开始
            is_new_entry = False
            for keyword in start_keywords:
                if keyword in line:
                    # 额外检查：确保这不像是一个子描述
                    if len(line) < 80 or line.index(keyword) < 40:
                        is_new_entry = True
                        break

            # 检查时间模式作为条目开始
            if not is_new_entry:
                if re.match(r'^(20\d{2}|\d{4})[\.\-/年]', line) or \
                   re.match(r'^(20\d{2})\s*[\-–~]\s*(20\d{2}|至今|Present)', line, re.IGNORECASE):
                    is_new_entry = True

            if is_new_entry and current_entry:
                entries.append('\n'.join(current_entry))
                current_entry = []

            current_entry.append(line)
            i += 1

        if current_entry:
            entries.append('\n'.join(current_entry))

        return entries

    def _parse_education_entry(self, entry_text: str) -> Dict[str, Any]:
        """解析单个教育条目"""
        edu_item = {
            "school": "",
            "degree": "",
            "field": "",
            "start_date": "",
            "end_date": ""
        }

        lines = entry_text.split('\n')
        full_text = entry_text

        # 提取学校名称
        school_patterns = [
            r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))',
            r'([\u4e00-\u9fa5]{2,20}(?:University|College|Institute|School)[^\n,]*?)',
            r'([^\n,]*(?:University|College|Institute|School)\s+(?:of\s+)?[\w\s]+)',
        ]

        for pattern in school_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                school = match.group(1).strip()
                if len(school) > 2 and len(school) < 60:
                    edu_item['school'] = school
                    break

        # 提取学位
        degree_map = {
            '博士': ['博士', 'PhD', 'Ph.D', 'Doctor', 'Doctorate'],
            '硕士': ['硕士', 'Master', 'MBA', 'EMBA', '硕士研究生'],
            '本科': ['本科', '学士', 'Bachelor', 'Undergraduate'],
            '专科': ['专科', '大专', 'Associate']
        }

        for degree_name, keywords in degree_map.items():
            for keyword in keywords:
                if keyword in full_text:
                    edu_item['degree'] = degree_name
                    break
            if edu_item['degree']:
                break

        # 提取专业/领域
        field_patterns = [
            r'(?:专业|Major|Field)[:：\s]*([\u4e00-\u9fa5]{2,15})',
            r'(?:学士|硕士|博士)\s*(?:学位)?[:：\s]*([\u4e00-\u9fa5]{2,15})',
            r'([\u4e00-\u9fa5]{2,10}(?:学|工程|技术|科学|管理))',
        ]

        for pattern in field_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                field = match.group(1).strip()
                if len(field) > 1 and len(field) < 30 and field not in ['专业', '学位']:
                    edu_item['field'] = field
                    break

        # 提取时间
        date_patterns = [
            # 2018.09 - 2022.06
            r'(20\d{2})[\.\-/年](\d{1,2})?\s*[\-–~]\s*(20\d{2})?[\.\-/年]?(\d{1,2}|至今|Present)?',
            # 2018 - 2022
            r'(20\d{2})\s*[\-–~]\s*(20\d{2}|至今|Present)',
            # 2018年9月 - 2022年6月
            r'(20\d{2})年(?:\d{1,2}月)?\s*[\-–~]\s*(?:(20\d{2})年)?(?:至今)?',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups[0]:
                    edu_item['start_date'] = groups[0]
                if len(groups) > 1 and groups[-1]:
                    end_part = groups[-1]
                    if '至今' in str(end_part) or 'Present' in str(end_part):
                        edu_item['end_date'] = '至今'
                    elif re.match(r'20\d{2}', str(end_part)):
                        edu_item['end_date'] = end_part
                break

        return edu_item

    def _extract_experiences(self, text: str) -> List[Dict[str, Any]]:
        """提取工作经历 - 增强版，支持多行解析和多种格式"""
        experiences = []

        # 工作经历相关关键词
        exp_keywords = ['工作经验', '工作经历', 'Work Experience', 'Experience', 'EXPERIENCE', '职业经历', '实习经历']

        # 查找工作经历部分
        exp_section = self._find_section(text, exp_keywords)
        if not exp_section:
            # 尝试通过公司关键词查找
            exp_section = text

        # 公司关键词作为条目分隔
        company_keywords = ['公司', '集团', '科技', '网络', '软件', '互联网',
                           'Corp', 'Inc', 'Ltd', 'LLC', 'Co.', 'Company']

        entries = self._split_into_entries(exp_section, company_keywords)

        for entry in entries[:15]:  # 最多处理15个条目
            exp_item = self._parse_experience_entry(entry)
            if exp_item and exp_item.get('company'):
                experiences.append(exp_item)

        logger.info(f"Extracted {len(experiences)} experience entries")
        return experiences[:10]

    def _parse_experience_entry(self, entry_text: str) -> Dict[str, Any]:
        """解析单个工作经历条目"""
        exp_item = {
            "company": "",
            "title": "",
            "start_date": "",
            "end_date": "",
            "projects": []
        }

        lines = entry_text.split('\n')
        full_text = entry_text

        # 提取公司名称
        company_patterns = [
            r'([^\n]*(?:公司|集团|科技|网络|软件|互联网|Corp|Inc|Ltd|LLC)[^\n,]*)',
            r'(?:公司|单位|组织)[:\s]*([^\n]+)',
            r'^([^\n]{2,30}(?:公司|集团))',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                company = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                company = re.sub(r'^(?:公司|单位)[:\s]*', '', company, flags=re.IGNORECASE)
                if len(company) > 2 and len(company) < 80:
                    exp_item['company'] = company
                    break

        # 提取职位
        title_keywords = ['工程师', '开发', '经理', '主管', '总监', '架构师', '负责人', '专员',
                         'Engineer', 'Developer', 'Manager', 'Lead', 'Director', 'Architect',
                         'Analyst', 'Consultant', 'Specialist', 'Coordinator']

        title_patterns = [
            r'(?:职位|岗位|职务|Title)[:\s]*([^\n]+)',
            r'((?:高级|资深|初级|助理)?\s*[^\n]{2,20}(?:工程师|开发|经理|主管|总监|架构师|负责人))',
            r'((?:Senior|Junior|Lead|Principal)?\s*[\w\s]+(?:Engineer|Developer|Manager|Analyst))',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                title = re.sub(r'^(?:职位|岗位|职务)[:\s]*', '', title, flags=re.IGNORECASE)
                if len(title) > 1 and len(title) < 50:
                    exp_item['title'] = title
                    break

        # 如果还没找到职位，尝试从关键词匹配
        if not exp_item['title']:
            for keyword in title_keywords:
                pattern = r'([^\n]*?' + keyword + r'[^\n]{0,10})'
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if 2 < len(title) < 40:
                        exp_item['title'] = title
                        break

        # 提取时间
        date_patterns = [
            # 2018.09 - 2022.06
            r'(20\d{2})[\.\-/年](\d{1,2})?\s*[\-–~]\s*(20\d{2})?[\.\-/年]?(\d{1,2}|至今|Present)?',
            # 2018 - 2022
            r'(20\d{2})\s*[\-–~]\s*(20\d{2}|至今|Present)',
            # 2018年9月 - 2022年6月
            r'(20\d{2})年(?:\d{1,2}月)?\s*[\-–~]\s*(?:(20\d{2})年)?(?:至今)?',
            # 09/2018 - 06/2022 (美式日期)
            r'(\d{1,2})[\/\.](20\d{2})\s*[\-–~]\s*(\d{1,2}|[\w]+)?[\/\.]?(20\d{2})?',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                # 处理不同格式的日期
                if groups[0] and re.match(r'20\d{2}', str(groups[0])):
                    exp_item['start_date'] = groups[0]
                    if len(groups) > 2 and groups[-1]:
                        end_part = groups[-1]
                        if re.match(r'20\d{2}', str(end_part)):
                            exp_item['end_date'] = end_part
                        elif '至今' in str(end_part) or 'Present' in str(end_part).capitalize():
                            exp_item['end_date'] = '至今'
                elif groups[0] and re.match(r'\d{1,2}', str(groups[0])) and len(groups) > 1:
                    # 美式日期格式
                    exp_item['start_date'] = groups[1]
                    if len(groups) > 3 and groups[3]:
                        exp_item['end_date'] = groups[3]
                break

        # 提取项目经历（在工作经历中）
        project_patterns = [
            r'(?:项目|Project)[:\s]*([^\n]+)',
        ]
        projects_found = []
        for pattern in project_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                project_name = match.group(1).strip()
                if len(project_name) > 1 and len(project_name) < 50:
                    projects_found.append({
                        "name": project_name,
                        "description": "",
                        "technologies": []
                    })

        if projects_found:
            exp_item['projects'] = projects_found[:3]  # 最多3个项目

        return exp_item

    def _extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """提取技能关键词 - 增强版，支持技能分区识别和智能分类"""

        # 技能词库 - 按类别组织
        skill_categories = {
            "programming_languages": {
                "keywords": ["Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Swift", "Kotlin",
                           "PHP", "Ruby", "Scala", "Perl", "R", "MATLAB", "Lua", "Shell", "Bash", "C", "Objective-C",
                           "Groovy", "Dart", "Julia", "Haskell", "Clojure"],
                "display_name": "编程语言"
            },
            "frontend": {
                "keywords": ["React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "jQuery", "Bootstrap",
                           "Tailwind CSS", "HTML", "CSS", "Sass", "Less", "Webpack", "Vite", "Parcel",
                           "Redux", "MobX", "Pinia", "Zustand", "jQuery UI", "Material-UI", "Ant Design",
                           "Element UI", "Chakra UI", "Styled Components"],
                "display_name": "前端技术"
            },
            "backend": {
                "keywords": ["Node.js", "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "Express",
                           "NestJS", "Laravel", "Rails", "ASP.NET", "gRPC", "GraphQL", "REST API",
                           "Rocket", "Actix", "Tornado", "Koa", "ThinkPHP", "CodeIgniter"],
                "display_name": "后端框架"
            },
            "databases": {
                "keywords": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
                           "Oracle", "SQL Server", "Cassandra", "DynamoDB", "Firebase", "Neo4j",
                           "ClickHouse", "InfluxDB", "TimescaleDB", "MariaDB", "CouchDB", "HBase"],
                "display_name": "数据库"
            },
            "ai_ml": {
                "keywords": ["TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
                           "Spark", "Hadoop", "Kafka", "Flink", "Airflow", "HBase", "Hive",
                           "XGBoost", "LightGBM", "CatBoost", "OpenCV", "NLTK", "SpaCy",
                           "Transformers", "BERT", "GPT", "LLM", "LangChain", "Pinecone", "Chroma"],
                "display_name": "AI/大数据"
            },
            "devops": {
                "keywords": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", "Travis CI",
                           "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云", "Heroku", "Vercel",
                           "Linux", "Nginx", "Apache", "Git", "SVN", "Terraform", "Ansible",
                           "Prometheus", "Grafana", "ELK", "Consul", "Vault", "Helm", "Istio"],
                "display_name": "DevOps/云"
            },
            "mobile": {
                "keywords": ["iOS", "Android", "React Native", "Flutter", "Swift", "Kotlin",
                           "Xamarin", "Ionic", "Cordova", "PhoneGap", "uni-app", "Taro"],
                "display_name": "移动端"
            },
            "testing": {
                "keywords": ["Jest", "Mocha", "Cypress", "Selenium", "Playwright", "Pytest",
                           "JUnit", "TestNG", "Cucumber", "Appium", "Postman", "JMeter",
                           "单元测试", "集成测试", "E2E测试", "自动化测试"],
                "display_name": "测试"
            },
            "tools": {
                "keywords": ["VS Code", "IntelliJ IDEA", "PyCharm", "WebStorm", "Eclipse", "Xcode",
                           "Jira", "Confluence", "Trello", "Notion", "Slack", "Teams",
                           "Figma", "Sketch", "Photoshop", "Postman", "Charles", "Wireshark"],
                "display_name": "工具"
            },
            "methodologies": {
                "keywords": ["Microservices", "CI/CD", "Agile", "Scrum", "TDD", "DDD", "DevOps",
                           "OOP", "Functional Programming", "Reactive Programming", "Event-Driven",
                           "SOA", "MVC", "MVVM", "Clean Architecture", "Design Patterns"],
                "display_name": "方法论"
            },
            "languages": {
                "keywords": ["英语", "English", "中文", "Chinese", "日语", "Japanese", "法语", "French",
                           "德语", "German", "西班牙语", "Spanish", "韩语", "Korean",
                           "普通话", "粤语", "CET-4", "CET-6", "TEM-4", "TEM-8", "雅思", "托福"],
                "display_name": "语言能力"
            }
        }

        skills = []

        # 查找技能部分
        skill_keywords = ['技能', '技能清单', 'Skills', 'SKILLS', '技术栈', 'Tech Stack', '专业技能']
        skill_section = self._find_section(text, skill_keywords)

        # 如果在技能部分找到内容，优先使用它
        if skill_section:
            search_text = skill_section
        else:
            search_text = text

        search_text_upper = search_text.upper()

        # 记录已找到的技能，避免重复
        found_skills = set()

        for category, data in skill_categories.items():
            for skill in data["keywords"]:
                # 使用单词边界匹配
                pattern = r'(?:^|[\s,，;；、]|\b)' + re.escape(skill.upper()) + r'(?:[\s,，;；、]|\b|$)'
                if re.search(pattern, search_text_upper):
                    if skill not in found_skills:
                        found_skills.add(skill)
                        skills.append({
                            "name": skill,
                            "level": self._infer_skill_level(search_text, skill),
                            "category": data["display_name"]
                        })

        # 如果技能太少，尝试从全文搜索
        if len(skills) < 5:
            full_text_upper = text.upper()
            for category, data in skill_categories.items():
                for skill in data["keywords"]:
                    if skill not in found_skills:
                        pattern = r'(?:^|[\s,，;；、]|\b)' + re.escape(skill.upper()) + r'(?:[\s,，;；、]|\b|$)'
                        if re.search(pattern, full_text_upper):
                            found_skills.add(skill)
                            skills.append({
                                "name": skill,
                                "level": self._infer_skill_level(text, skill),
                                "category": data["display_name"]
                            })

        # 按类别分组后按名称排序
        skills.sort(key=lambda x: (x["category"], len(x["name"])), reverse=False)

        logger.info(f"Extracted {len(skills)} skills")
        return skills[:40]  # 限制最多40个技能

    def _infer_skill_level(self, text: str, skill: str) -> str:
        """根据上下文推断技能熟练度"""
        # 查找技能附近的文本
        skill_pattern = r'[^。\n]*' + re.escape(skill) + r'[^。\n]*'
        matches = re.findall(skill_pattern, text, re.IGNORECASE)

        if not matches:
            return "熟练"

        context = ' '.join(matches).lower()

        # 熟练度关键词
        expert_keywords = ['精通', 'expert', '精通', 'master', '高级', 'advanced', '非常熟悉']
        proficient_keywords = ['熟练', 'proficient', '熟悉', 'familiar', '掌握', 'skilled', '中级', 'intermediate']
        beginner_keywords = ['了解', 'beginner', '入门', 'basic', '初级', '了解', '接触过']

        for keyword in expert_keywords:
            if keyword in context:
                return "精通"
        for keyword in beginner_keywords:
            if keyword in context:
                return "入门"
        for keyword in proficient_keywords:
            if keyword in context:
                return "熟练"

        return "熟练"

    def _extract_links(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取 LinkedIn 和个人网站链接"""
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile\?id=)([a-zA-Z0-9\-_]+)'
        website_patterns = [
            r'(https?://[^\s\n]+(?:github\.io|vercel\.app|netlify\.app|gitee\.io)[^\s\n]*)',
            r'(https?://[^\s\n]+(?:个人网站|portfolio|blog)[^\s\n]*)',
        ]

        linkedin = None
        website = None

        # 提取 LinkedIn
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            linkedin = f"https://linkedin.com/in/{linkedin_match.group(1)}"

        # 提取网站
        for pattern in website_patterns:
            website_match = re.search(pattern, text, re.IGNORECASE)
            if website_match:
                website = website_match.group(1)
                break

        return linkedin, website

    def extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        """
        从原始简历文本提取结构化数据 (v2 路径)
        使用 规则 + LLM 双通道 → result_fusion_v2 → 字段级置信度
        """
        import asyncio
        from app.services.resume_extraction.resume_extraction_service import extract_resume_text_v2
        logger.info(f"Starting v2 structured data extraction, text length: {len(raw_text)} chars")

        try:
            # 同步调用 v2 异步入口
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result = loop.run_until_complete(extract_resume_text_v2(raw_text, use_llm=True))
            data = result.get("data", {})

            # 兜底: 包含 v1 字段名 (frontend 兼容)
            if "personal_info" in data and isinstance(data["personal_info"], dict):
                pi = data["personal_info"]
                # 复制 education 字段为 educations (兼容)
                if "education" not in data and "educations" in data:
                    data["education"] = data["educations"]
                # 复制 experiences 字段为 work_experiences (兼容)
                if "experiences" not in data and "work_experiences" in data:
                    data["experiences"] = data["work_experiences"]

            quality = result.get("quality", {})
            logger.info(f"v2 extraction complete: name={data.get('personal_info', {}).get('name')}, "
                       f"education={len(data.get('educations', []))}, "
                       f"work={len(data.get('work_experiences', []))}, "
                       f"projects={len(data.get('projects', []))}, "
                       f"skills={len(data.get('skills', []))}, "
                       f"conf={quality.get('confidence_score', 0):.2f}")

            return data

        except Exception as e:
            # P0-3: 异常时降级到 _extract_structured_data_legacy（规则引擎），不再返回空 dict
            logger.warning(f"v2 extraction failed, fallback to legacy rule engine: {e}", exc_info=True)
            return self._extract_structured_data_legacy(raw_text)

    def _extract_structured_data_legacy(self, raw_text: str) -> Dict[str, Any]:
        """
        旧的结构化数据提取方法（作为备用）
        """
        logger.info(f"Starting legacy structured data extraction, text length: {len(raw_text)} chars")

        # 初始化结构化数据模板
        structured_data = {
            "personal_info": {
                "name": "",
                "email": "",
                "phone": "",
                "linkedin": None,
                "website": None
            },
            "education": [],
            "skills": [],
            "experiences": [],
            "raw_text_preview": ""
        }

        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, raw_text)
        if emails:
            structured_data["personal_info"]["email"] = emails[0]
            logger.debug(f"Found email: {emails[0]}")

        # 提取电话 (支持中国大陆手机号和座机)
        phone_patterns = [
            r'1[3-9]\d{9}',  # 手机号
            r'\d{3,4}-\d{7,8}',  # 座机
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, raw_text)
            if phones:
                structured_data["personal_info"]["phone"] = phones[0]
                logger.debug(f"Found phone: {phones[0]}")
                break

        # 提取姓名（增强版：支持多种姓名格式）
        lines = raw_text.split('\n')
        excluded_names = {'简历', '个人信息', '教育经历', '工作经验', '工作经历', '技能', '项目经验', '自我评价', '求职意向', '基本信息', '个人简介', '概况', 'Summary', 'Profile', 'Personal', 'Education', 'Experience', 'Skills', 'Contact'}

        # 尝试多种方式提取姓名
        name = ""

        # 方法1: 查找明确标记的姓名（如"姓名：张三"）
        name_patterns = [
            r'(?:姓名|名字|Name)[\s:：:]*([\u4e00-\u9fa5]{2,4}(?:·[\u4e00-\u9fa5]+)?)',
            r'(?:姓名|名字|Name)[\s:：:]*([A-Za-z\s\.]+[\u4e00-\u9fa5]*|[\u4e00-\u9fa5]+[A-Za-z\s]*)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                if len(potential_name) >= 2 and len(potential_name) <= 20 and potential_name not in excluded_names:
                    name = potential_name
                    logger.debug(f"Found name from pattern: {name}")
                    break

        # 方法2: 从邮箱前缀推断姓名（如果邮箱格式为 zhangsan@xxx 或 zhang.san@xxx）
        if not name and structured_data["personal_info"]["email"]:
            email_prefix = structured_data["personal_info"]["email"].split('@')[0]
            # 如果邮箱前缀是拼音格式（如 zhangsan, zhang.san, zhang_san）
            if re.match(r'^[a-zA-Z]+[\._]?[a-zA-Z]*$', email_prefix) and len(email_prefix) >= 4:
                # 尝试提取可能的姓名，但不直接使用作为最终姓名
                logger.debug(f"Email prefix hint: {email_prefix}")

        # 方法3: 检查前30行，寻找可能的姓名（改进版）
        if not name:
            for i, line in enumerate(lines[:30]):  # 扩展到前30行
                line = line.strip()
                if not line or len(line) > 20:
                    continue

                # 匹配纯中文姓名（2-4个汉字）
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', line) and line not in excluded_names:
                    # 额外检查：避免匹配到职位、公司等
                    if not any(keyword in line for keyword in ['工程师', '经理', '主管', '总监', '公司', '科技', '有限']):
                        name = line
                        logger.debug(f"Found Chinese name from line {i}: {name}")
                        break

        # 方法4: 匹配中英文混合姓名（如 "张三 John Zhang"）
        if not name:
            for line in lines[:20]:
                line = line.strip()
                # 匹配模式：中文名 + 英文名 或 英文名 + 中文名
                mixed_match = re.match(r'^([\u4e00-\u9fa5]{2,4})\s*[A-Za-z\s]*$|^([A-Za-z\s]+)\s*[\u4e00-\u9fa5]{2,4}$', line)
                if mixed_match:
                    potential_name = mixed_match.group(1) or mixed_match.group(2)
                    potential_name = potential_name.strip()
                    if potential_name and potential_name not in excluded_names and len(potential_name) <= 20:
                        name = potential_name
                        logger.debug(f"Found mixed name: {name}")
                        break

        # 方法5: 从第一行提取（如果第一行是简短的文本且不像标题）
        if not name and lines:
            first_line = lines[0].strip()
            if (first_line and
                len(first_line) < 30 and
                not any(c in first_line for c in ['@', 'http', '电话', '手机', '：', ':']) and
                first_line not in excluded_names and
                not re.search(r'(公司|集团|科技|网络|软件|互联网|简历|求职|应聘)', first_line)):
                name = first_line
                logger.debug(f"Found name from first line: {name}")

        structured_data["personal_info"]["name"] = name

        # 提取链接
        linkedin, website = self._extract_links(raw_text)
        structured_data["personal_info"]["linkedin"] = linkedin
        structured_data["personal_info"]["website"] = website
        if linkedin:
            logger.debug(f"Found LinkedIn: {linkedin}")
        if website:
            logger.debug(f"Found website: {website}")

        # 提取教育经历
        structured_data["education"] = self._extract_education(raw_text)

        # 提取工作经历
        structured_data["experiences"] = self._extract_experiences(raw_text)

        # 提取技能
        structured_data["skills"] = self._extract_skills(raw_text)

        # 保存原始文本预览
        structured_data["raw_text_preview"] = raw_text[:3000] if len(raw_text) > 3000 else raw_text

        logger.info(f"Legacy extraction complete: name={structured_data['personal_info']['name']}, "
                   f"education={len(structured_data['education'])}, "
                   f"experiences={len(structured_data['experiences'])}, "
                   f"skills={len(structured_data['skills'])}")

        return structured_data

    def get_vault_by_user_id(self, user_id: str) -> Optional[CareerVault]:
        """通过用户 ID 获取 Career Vault"""
        return self.db.query(CareerVault).filter(CareerVault.user_id == user_id).first()

    def create_vault(self, user_id: str, vault_data: CareerVaultCreate) -> CareerVault:
        """创建 Career Vault"""
        db_vault = CareerVault(
            user_id=user_id,
            structured_data=vault_data.structured_data
        )
        self.db.add(db_vault)
        self.db.commit()
        self.db.refresh(db_vault)
        return db_vault

    def update_vault(self, vault: CareerVault, vault_data: CareerVaultUpdate) -> CareerVault:
        """更新 Career Vault"""
        if vault_data.structured_data is not None:
            import json
            old_data = json.dumps(vault.structured_data, sort_keys=True, ensure_ascii=False) if vault.structured_data else ""
            new_data = json.dumps(vault_data.structured_data, sort_keys=True, ensure_ascii=False)
            if old_data != new_data:
                vault.structured_data = vault_data.structured_data
                vault.version += 1
                vault.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(vault)
        return vault

    def delete_vault(self, vault: CareerVault) -> None:
        """删除 Career Vault"""
        self.db.delete(vault)
        self.db.commit()

    def process_resume_upload(self, user_id: str, file: UploadFile) -> CareerVault:
        """
        处理简历上传的完整流程
        1. 解析文件获取原始文本
        2. 提取结构化数据
        3. 创建或更新 Vault
        """
        # 解析文件
        raw_content = self.parse_resume_file(file)

        if not raw_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法从文件中提取文本，请确保文件内容有效"
            )

        # 提取结构化数据
        structured_data = self.extract_structured_data(raw_content)

        # 检查是否已存在 Vault
        existing_vault = self.get_vault_by_user_id(user_id)

        if existing_vault:
            # 更新现有 Vault
            existing_vault.raw_content = raw_content
            existing_vault.structured_data = structured_data
            existing_vault.version += 1
            existing_vault.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_vault)
            return existing_vault
        else:
            # 创建新 Vault
            from app.schemas.vault import CareerVaultCreate
            vault_data = CareerVaultCreate(structured_data=structured_data)
            new_vault = self.create_vault(user_id, vault_data)
            # 更新 raw_content
            new_vault.raw_content = raw_content
            self.db.commit()
            self.db.refresh(new_vault)
            return new_vault
