"""
防幻觉校验服务 - 确保AI生成的简历内容基于真实经历

核心功能：
1. 技术名词提取与索引
2. 生成内容校验
3. 幻觉检测告警
"""

import re
import json
import logging
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HallucinationLevel(Enum):
    """幻觉严重程度级别"""
    NONE = "none"           # 无幻觉
    LOW = "low"             # 轻微（措辞调整）
    MEDIUM = "medium"       # 中等（技能夸大）
    HIGH = "high"           # 严重（虚构经历）


@dataclass
class HallucinationCheckResult:
    """幻觉校验结果"""
    has_hallucination: bool
    level: HallucinationLevel
    suspicious_terms: List[Dict[str, Any]]
    confidence_score: float  # 0-1，越高表示越可能是幻觉
    suggestions: List[str]


class HallucinationService:
    """防幻觉校验服务"""
    
    # 扩展的技术关键词库
    TECH_KEYWORDS = {
        # 编程语言
        "languages": {
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl",
            "Lua", "Shell", "Bash", "PowerShell", "SQL", "NoSQL", "HTML", "CSS",
            "Sass", "Less", "C", "Objective-C", "Dart", "Elixir", "Clojure",
            "Haskell", "F#", "VB.NET", "Assembly", "Groovy", "Julia"
        },
        # 前端框架/库
        "frontend": {
            "React", "Vue", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js",
            "Gatsby", "Remix", "Preact", "jQuery", "Bootstrap", "Tailwind CSS",
            "Material-UI", "Ant Design", "Chakra UI", "Styled Components",
            "Redux", "Vuex", "Pinia", "Zustand", "React Query", "SWR",
            "Webpack", "Vite", "Rollup", "Parcel", "esbuild", "Babel",
            "TypeScript", "Flow", "CoffeeScript", "Elm", "PureScript"
        },
        # 后端框架
        "backend": {
            "Django", "Flask", "FastAPI", "Tornado", "Spring", "Spring Boot",
            "Spring Cloud", "Express", "Koa", "NestJS", "Hapi", "Fastify",
            "Ruby on Rails", "Sinatra", "Laravel", "Symfony", "CodeIgniter",
            "ASP.NET", "ASP.NET Core", "Phoenix", "Rocket", "Actix",
            "GraphQL", "REST API", "gRPC", "WebSocket", "SOAP", "tRPC"
        },
        # 数据库
        "database": {
            "MySQL", "PostgreSQL", "SQLite", "Oracle", "SQL Server", "MongoDB",
            "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "Firestore",
            "CouchDB", "Neo4j", "InfluxDB", "TimescaleDB", "ClickHouse",
            "Snowflake", "BigQuery", "Redshift", "Supabase", "Prisma",
            "Sequelize", "SQLAlchemy", "Hibernate", "TypeORM", "Mongoose"
        },
        # 云与DevOps
        "cloud_devops": {
            "AWS", "Amazon Web Services", "EC2", "S3", "Lambda", "ECS", "EKS",
            "Azure", "GCP", "Google Cloud", "阿里云", "腾讯云", "华为云",
            "Docker", "Kubernetes", "K8s", "Helm", "Terraform", "Ansible",
            "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
            "Prometheus", "Grafana", "ELK Stack", "Datadog", "New Relic",
            "Nginx", "Apache", "HAProxy", "CDN", "CloudFront", "Cloudflare"
        },
        # AI/ML
        "ai_ml": {
            "Machine Learning", "Deep Learning", "Neural Networks", "CNN", "RNN",
            "Transformer", "BERT", "GPT", "LLM", "Large Language Model",
            "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
            "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
            "OpenCV", "PIL", "NLTK", "SpaCy", "Hugging Face", "LangChain",
            "Computer Vision", "NLP", "Natural Language Processing",
            "Reinforcement Learning", "GAN", "VAE", "Diffusion Models"
        },
        # 大数据
        "bigdata": {
            "Hadoop", "Spark", "Flink", "Kafka", "Storm", "Hive", "Pig",
            "HBase", "Cassandra", "Airflow", "Prefect", "Dagster",
            "dbt", "Great Expectations", "Pandas", "Dask", "Ray",
            "Data Pipeline", "ETL", "ELT", "Data Warehouse", "Data Lake"
        },
        # 移动端
        "mobile": {
            "iOS", "Android", "React Native", "Flutter", "Swift", "Kotlin",
            "Objective-C", "Java Mobile", "Xamarin", "Ionic", "Cordova",
            "PhoneGap", "Capacitor", "SwiftUI", "Jetpack Compose"
        },
        # 测试
        "testing": {
            "Unit Testing", "Integration Testing", "E2E Testing", "Jest",
            "Mocha", "Chai", "Cypress", "Playwright", "Selenium", "Puppeteer",
            "Pytest", "JUnit", "TestNG", "Cucumber", "Gherkin",
            "TDD", "BDD", "Test Coverage", "Mock", "Stub", "Fake"
        },
        # 安全
        "security": {
            "OAuth", "JWT", "SSO", "SAML", "LDAP", "Active Directory",
            "SSL/TLS", "HTTPS", "Encryption", "Hashing", "Penetration Testing",
            "Vulnerability Scanning", "OWASP", "CORS", "CSRF", "XSS",
            "Security Audit", "Compliance", "GDPR", "HIPAA", "SOC2"
        },
        # 项目管理
        "project_management": {
            "Agile", "Scrum", "Kanban", "Lean", "Waterfall", "SAFe",
            "Jira", "Confluence", "Trello", "Asana", "Monday", "Notion",
            "Sprint", "Backlog", "User Story", "Epic", "Roadmap",
            "Product Manager", "Project Manager", "Tech Lead", "Scrum Master"
        },
        # 软技能
        "soft_skills": {
            "Leadership", "Communication", "Teamwork", "Problem Solving",
            "Critical Thinking", "Time Management", "Adaptability",
            "Conflict Resolution", "Stakeholder Management", "Mentoring",
            "Cross-functional Collaboration", "Presentation Skills"
        }
    }
    
    def __init__(self):
        # 构建扁平化的技术词汇库
        self.tech_vocabulary = self._build_vocabulary()
        # 编译正则表达式模式
        self.tech_pattern = self._compile_tech_pattern()
        
    def _build_vocabulary(self) -> Set[str]:
        """构建扁平化的技术词汇库"""
        vocabulary = set()
        for category, terms in self.TECH_KEYWORDS.items():
            vocabulary.update(terms)
        return vocabulary
    
    def _compile_tech_pattern(self) -> re.Pattern:
        """编译技术名词匹配正则表达式"""
        # 按长度降序排序，优先匹配更长的术语
        sorted_terms = sorted(self.tech_vocabulary, key=len, reverse=True)
        # 转义特殊字符
        escaped_terms = [re.escape(term) for term in sorted_terms]
        # 构建正则表达式（不区分大小写）
        pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def extract_tech_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取技术名词
        
        Returns:
            List[Dict]: 包含术语、类别、位置的信息
        """
        if not text:
            return []
        
        terms = []
        seen = set()
        
        # 使用正则表达式匹配
        for match in self.tech_pattern.finditer(text):
            term = match.group(0)
            term_lower = term.lower()
            
            if term_lower not in seen:
                seen.add(term_lower)
                category = self._get_term_category(term)
                terms.append({
                    "term": term,
                    "category": category,
                    "position": match.span(),
                    "confidence": 1.0  # 直接匹配的高置信度
                })
        
        # 按位置排序
        terms.sort(key=lambda x: x["position"][0])
        return terms
    
    def _get_term_category(self, term: str) -> str:
        """获取术语所属类别"""
        term_lower = term.lower()
        for category, terms in self.TECH_KEYWORDS.items():
            if any(t.lower() == term_lower for t in terms):
                return category
        return "unknown"
    
    def build_vault_index(self, vault_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建Career Vault的技术名词索引
        
        Args:
            vault_data: Vault数据结构
            
        Returns:
            Dict: 包含所有技术名词的索引
        """
        index = {
            "all_terms": set(),
            "by_category": {},
            "by_source": {
                "skills": [],
                "experiences": [],
                "projects": [],
                "education": []
            },
            "raw_text": ""
        }
        
        # 提取所有文本
        text_parts = []
        
        # 从技能中提取
        if "skills" in vault_data:
            for skill in vault_data["skills"]:
                skill_name = skill.get("name", "")
                if skill_name:
                    text_parts.append(skill_name)
                    terms = self.extract_tech_terms(skill_name)
                    for term in terms:
                        index["all_terms"].add(term["term"].lower())
                        index["by_source"]["skills"].append(term)
        
        # 从经历中提取
        if "experiences" in vault_data:
            for exp in vault_data["experiences"]:
                # 公司名和职位
                company = exp.get("company", "")
                title = exp.get("title", "")
                text_parts.extend([company, title])
                
                # 项目描述
                for project in exp.get("projects", []):
                    desc = project.get("description", "")
                    techs = project.get("technologies", [])
                    text_parts.append(desc)
                    text_parts.extend(techs)
                    
                    # 提取技术名词
                    full_text = desc + " " + " ".join(techs)
                    terms = self.extract_tech_terms(full_text)
                    for term in terms:
                        index["all_terms"].add(term["term"].lower())
                        index["by_source"]["projects"].append(term)
        
        # 从教育背景中提取
        if "education" in vault_data:
            for edu in vault_data["education"]:
                school = edu.get("school", "")
                field = edu.get("field", "")
                text_parts.extend([school, field])
        
        index["raw_text"] = " ".join(text_parts)
        
        # 按类别分组
        for source, terms in index["by_source"].items():
            for term in terms:
                cat = term["category"]
                if cat not in index["by_category"]:
                    index["by_category"][cat] = set()
                index["by_category"][cat].add(term["term"].lower())
        
        # 将set转换为list以便JSON序列化
        index["all_terms"] = list(index["all_terms"])
        for cat in index["by_category"]:
            index["by_category"][cat] = list(index["by_category"][cat])
        
        return index
    
    def check_hallucination(
        self,
        generated_content: str,
        vault_index: Dict[str, Any],
        strict_mode: bool = True
    ) -> HallucinationCheckResult:
        """
        检查生成内容是否存在幻觉
        
        Args:
            generated_content: AI生成的简历内容
            vault_index: Vault技术名词索引
            strict_mode: 是否使用严格模式
            
        Returns:
            HallucinationCheckResult: 校验结果
        """
        suspicious_terms = []
        vault_terms = set(t.lower() for t in vault_index.get("all_terms", []))
        
        # 提取生成内容中的技术名词
        generated_terms = self.extract_tech_terms(generated_content)
        
        # 检查每个术语
        for term_info in generated_terms:
            term = term_info["term"]
            term_lower = term.lower()
            
            # 检查是否在Vault中
            if term_lower not in vault_terms:
                # 进一步检查是否是合理的变体
                if not self._is_reasonable_variant(term, vault_terms):
                    suspicious_terms.append({
                        "term": term,
                        "category": term_info["category"],
                        "position": term_info["position"],
                        "reason": "未在Career Vault中找到",
                        "suggestion": f"请确认是否掌握{term}，或从Vault中添加相关经历"
                    })
        
        # 检查虚构的项目或公司
        project_hallucinations = self._check_project_hallucinations(
            generated_content, vault_index
        )
        suspicious_terms.extend(project_hallucinations)
        
        # 计算置信度分数
        confidence_score = self._calculate_confidence(
            len(generated_terms),
            len(suspicious_terms)
        )
        
        # 确定幻觉级别
        level = self._determine_level(
            len(suspicious_terms),
            confidence_score,
            strict_mode
        )
        
        # 生成建议
        suggestions = self._generate_suggestions(suspicious_terms, level)
        
        return HallucinationCheckResult(
            has_hallucination=len(suspicious_terms) > 0,
            level=level,
            suspicious_terms=suspicious_terms,
            confidence_score=confidence_score,
            suggestions=suggestions
        )
    
    def _is_reasonable_variant(self, term: str, vault_terms: Set[str]) -> bool:
        """检查是否是合理的术语变体"""
        term_lower = term.lower()
        
        # 常见变体映射
        variants = {
            "react.js": "react",
            "vue.js": "vue",
            "node.js": "node",
            "next.js": "next",
            "nuxt.js": "nuxt",
            "express.js": "express",
            "nest.js": "nest",
            "gatsby.js": "gatsby",
            "aws lambda": "lambda",
            "amazon s3": "s3",
            "amazon ec2": "ec2",
            "google cloud": "gcp",
            "azure devops": "devops",
            "machine learning": "ml",
            "deep learning": "dl",
            "natural language processing": "nlp",
            "artificial intelligence": "ai",
            "ci/cd": "cicd",
            "restful api": "rest api",
            "web api": "api",
            "unit test": "unit testing",
            "e2e test": "e2e testing",
            "integration test": "integration testing"
        }
        
        # 检查是否是已知变体
        if term_lower in variants:
            return variants[term_lower] in vault_terms
        
        # 检查是否是子串匹配
        for vault_term in vault_terms:
            if term_lower in vault_term or vault_term in term_lower:
                return True
        
        return False
    
    def _check_project_hallucinations(
        self,
        content: str,
        vault_index: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检查虚构的项目或公司"""
        suspicious = []
        
        # 提取项目描述模式
        project_patterns = [
            r'负责[了]?([^，。\n]+?)(?:项目|系统|平台)',
            r'参与[了]?([^，。\n]+?)(?:项目|系统|平台)',
            r'主导[了]?([^，。\n]+?)(?:项目|系统|平台)',
            r'开发[了]?([^，。\n]+?)(?:项目|系统|平台)',
            r'设计[了]?([^，。\n]+?)(?:项目|系统|平台)',
        ]
        
        vault_text = vault_index.get("raw_text", "").lower()
        
        for pattern in project_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                project_name = match.group(1).strip()
                if project_name and len(project_name) > 3:
                    # 检查是否在Vault中提及
                    if project_name.lower() not in vault_text:
                        suspicious.append({
                            "term": project_name,
                            "category": "project",
                            "position": match.span(),
                            "reason": "未在原始简历中提及的项目/系统",
                            "suggestion": "请确认该项目是否真实存在"
                        })
        
        return suspicious
    
    def _calculate_confidence(
        self,
        total_terms: int,
        suspicious_count: int
    ) -> float:
        """计算置信度分数"""
        if total_terms == 0:
            return 1.0
        
        # 可疑术语比例越低，置信度越高
        ratio = suspicious_count / total_terms
        confidence = 1.0 - ratio
        return max(0.0, min(1.0, confidence))
    
    def _determine_level(
        self,
        suspicious_count: int,
        confidence_score: float,
        strict_mode: bool
    ) -> HallucinationLevel:
        """确定幻觉级别"""
        if suspicious_count == 0:
            return HallucinationLevel.NONE
        
        # 严格模式阈值更严格
        if strict_mode:
            if confidence_score < 0.7 or suspicious_count >= 5:
                return HallucinationLevel.HIGH
            elif confidence_score < 0.85 or suspicious_count >= 3:
                return HallucinationLevel.MEDIUM
            else:
                return HallucinationLevel.LOW
        else:
            if confidence_score < 0.6 or suspicious_count >= 7:
                return HallucinationLevel.HIGH
            elif confidence_score < 0.8 or suspicious_count >= 4:
                return HallucinationLevel.MEDIUM
            else:
                return HallucinationLevel.LOW
    
    def _generate_suggestions(
        self,
        suspicious_terms: List[Dict[str, Any]],
        level: HallucinationLevel
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if level == HallucinationLevel.NONE:
            suggestions.append("✅ 未发现明显的幻觉内容，简历基于真实经历")
            return suggestions
        
        # 按类别分组
        by_category = {}
        for term in suspicious_terms:
            cat = term["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(term["term"])
        
        # 生成具体建议
        if "languages" in by_category or "frontend" in by_category or "backend" in by_category:
            suggestions.append(
                f"⚠️ 检测到 {len(by_category.get('languages', []) + by_category.get('frontend', []) + by_category.get('backend', []))} 个技术栈可能不在您的经历中，"
                f"建议：在Career Vault中补充相关项目经验，或从简历中移除"
            )
        
        if "project" in by_category:
            projects = by_category["project"]
            suggestions.append(
                f"⚠️ 检测到 {len(projects)} 个可能虚构的项目/系统：{', '.join(projects[:3])}，"
                f"建议：使用Vault中真实存在的项目名称"
            )
        
        if level == HallucinationLevel.HIGH:
            suggestions.append(
                "🔴 幻觉风险较高！建议重新生成简历，确保所有内容基于Career Vault中的真实经历"
            )
        elif level == HallucinationLevel.MEDIUM:
            suggestions.append(
                "🟡 存在中等幻觉风险，建议仔细核对上述内容"
            )
        else:
            suggestions.append(
                "🟢 幻觉风险较低，主要是措辞调整，可以接受"
            )
        
        suggestions.append(
            "💡 提示：您可以使用Copilot Chat对具体段落进行微调，确保内容真实准确"
        )
        
        return suggestions
    
    def verify_resume_generation(
        self,
        original_vault: Dict[str, Any],
        generated_resume: str,
        return_details: bool = False
    ) -> Dict[str, Any]:
        """
        完整的简历生成验证流程
        
        Args:
            original_vault: 原始Vault数据
            generated_resume: 生成的简历
            return_details: 是否返回详细信息
            
        Returns:
            Dict: 验证结果
        """
        # 构建Vault索引
        vault_index = self.build_vault_index(original_vault)
        
        # 执行幻觉检查
        check_result = self.check_hallucination(
            generated_resume,
            vault_index,
            strict_mode=True
        )
        
        result = {
            "verified": not check_result.has_hallucination or check_result.level in [
                HallucinationLevel.NONE, HallucinationLevel.LOW
            ],
            "hallucination_level": check_result.level.value,
            "confidence_score": round(check_result.confidence_score, 2),
            "suspicious_count": len(check_result.suspicious_terms),
            "suggestions": check_result.suggestions
        }
        
        if return_details:
            result["details"] = {
                "vault_terms_count": len(vault_index["all_terms"]),
                "generated_terms": [
                    {"term": t["term"], "category": t["category"]}
                    for t in self.extract_tech_terms(generated_resume)
                ],
                "suspicious_terms": check_result.suspicious_terms
            }
        
        return result


# 单例模式
_hallucination_service = None

def get_hallucination_service() -> HallucinationService:
    """获取防幻觉服务单例"""
    global _hallucination_service
    if _hallucination_service is None:
        _hallucination_service = HallucinationService()
    return _hallucination_service
