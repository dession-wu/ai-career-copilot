"""
简历信息提取配置
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """PDF解析器配置"""
    # 引擎优先级
    engine_priority: List[str] = field(default_factory=lambda: [
        "pdfplumber",  # 首选：速度快，保留布局
        "pymupdf",     # 备选：功能全面
        "marker",      # 兜底：复杂布局
    ])
    
    # 文本提取配置
    extract_layout: bool = True
    extract_images: bool = False  # 是否提取图片
    extract_tables: bool = True
    
    # 扫描件检测阈值
    scanned_pdf_threshold: float = 0.7  # 图片密度阈值
    min_text_ratio: float = 0.1  # 最小文本比例


@dataclass
class OCRConfig:
    """OCR配置"""
    # 引擎选择
    engine: str = "paddleocr"  # paddleocr / tesseract / easyocr
    
    # 语言支持
    languages: List[str] = field(default_factory=lambda: ["ch", "en"])
    
    # 预处理配置
    enable_preprocessing: bool = True
    auto_rotate: bool = True
    denoise: bool = True
    binarize: bool = False
    
    # 性能配置
    batch_size: int = 4
    num_workers: int = 2
    
    # 置信度阈值
    min_confidence: float = 0.6


@dataclass
class LayoutConfig:
    """版面分析配置 - 增强章节识别"""
    # 章节标题关键词 - 扩展版本，支持更多变体
    section_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "education": [
            "教育背景", "教育经历", "学历", "Education", "Academic Background",
            "EDUCATION", "教育", "学习经历", "教育情况", "学术背景",
            "教 育 背 景", "教 育 经 历", "学 历", "EDUCATION BACKGROUND",
            "就读院校", "毕业院校", "学校", "院校"
        ],
        "work_experience": [
            "工作经验", "工作经历", "Work Experience", "Experience",
            "EXPERIENCE", "职业经历", "实习经历", "工作实践", "实践经历",
            "工 作 经 验", "工 作 经 历", "工 作 实 践", "WORK EXPERIENCE",
            "实习经验", "职业经验", "工作履历", "履历"
        ],
        "projects": [
            "项目经历", "项目经验", "Projects", "Project Experience",
            "PROJECTS", "项目", "主要项目", "项目实践", "课题经历",
            "项 目 经 历", "项 目 经 验", "PROJECT EXPERIENCE",
            "研究项目", "课题项目", "实践项目", "项目成果"
        ],
        "skills": [
            "技能", "技能清单", "Skills", "Technical Skills",
            "SKILLS", "技术栈", "专业技能", "职业技能", "个人技能",
            "技 能", "技 能 清 单", "SKILL SET", "TECHNICAL SKILLS",
            "技术能力", "技术特长", "技能特长", "专业能力"
        ],
        "certifications": [
            "证书", "Certifications", "Certification", "CERTIFICATIONS",
            "资格证书", "职业证书", "认证", "资质证书",
            "证 书", "资 格 证 书", "CERTIFICATION",
            "专业认证", "技能认证", "职业认证"
        ],
        "languages": [
            "语言能力", "Languages", "Language Skills", "LANGUAGES",
            "外语", "语言", "外语能力", "语言技能",
            "语 言 能 力", "LANGUAGE SKILLS", "外语水平", "语言水平"
        ],
        "awards": [
            "奖项荣誉", "获奖情况", "Awards", "Honors", "AWARDS",
            "荣誉", "获奖", "奖励", "荣誉称号",
            "奖 项 荣 誉", "获 奖 情 况", "HONORS AND AWARDS",
            "所获荣誉", "获得奖项", "竞赛获奖"
        ],
        "self_evaluation": [
            "自我评价", "个人评价", "Self Evaluation", "Summary",
            "个人简介", "自我介绍", "概况", "个人总结",
            "自 我 评 价", "个 人 评 价", "SELF EVALUATION",
            "个人描述", "自我描述", "个人特质"
        ],
    })
    
    # 条目分隔模式
    entry_separators: List[str] = field(default_factory=lambda: [
        r"\n\n",  # 空行
        r"(?=20\d{2}[\.\-/年])",  # 时间开头
        r"(?=[•\-\*])",  # 列表符号
    ])


@dataclass
class ExtractionConfig:
    """信息提取配置"""
    # 提取策略
    strategy: str = "hybrid"  # rule / llm / hybrid
    
    # 规则引擎配置
    rule_engine_priority: bool = True
    
    # LLM配置
    llm_fallback: bool = True
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # 置信度阈值
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.6
    low_confidence_threshold: float = 0.4
    
    # 字段验证规则
    validation_rules: Dict[str, Dict] = field(default_factory=lambda: {
        "name": {
            "min_length": 2,
            "max_length": 20,
            "required": True,
        },
        "email": {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "required": False,
        },
        "phone": {
            "pattern": r"1[3-9]\d{9}",
            "required": False,
        },
    })


@dataclass
class SkillConfig:
    """技能提取配置 - 修复技能识别问题 - 全面扩展版本"""
    
    # 技能词库 - 全面扩展版本，覆盖更多技能
    skill_categories: Dict[str, Dict] = field(default_factory=lambda: {
        "programming_languages": {
            "keywords": [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
                "Swift", "Kotlin", "PHP", "Ruby", "Scala", "Perl", "R", "MATLAB", "Lua",
                "Shell", "Bash", "C", "Objective-C", "Groovy", "Dart", "Julia", "Haskell",
                "Clojure", "VB.NET", "Assembly", "COBOL", "Fortran", "Lisp", "Prolog",
                "SQL", "PL/SQL", "T-SQL", "NoSQL", "R语言", "Python语言"
            ],
            "display_name": "编程语言",
            "aliases": {
                "Python": ["python", "py", "Python语言", "PYTHON", "python3", "py3"],
                "JavaScript": ["javascript", "js", "JS", "Javascript", "JAVASCRIPT", "es6", "es2015"],
                "TypeScript": ["typescript", "ts", "TS", "Typescript", "TYPESCRIPT"],
                "C++": ["cpp", "cplusplus", "C++", "CPP", "c plus plus", "c++11", "c++14", "c++17", "c++20"],
                "C#": ["csharp", "cs", "C#", "CSHARP", "C SHARP", "dotnet", ".NET", ".net"],
                "MATLAB": ["matlab", "Matlab", "MATLAB", "MatLab"],
                "R": ["R语言", "r语言", "R", "r lang"],
                "Java": ["java", "JAVA", "Java语言", "java8", "java11", "java17"],
                "Go": ["go", "GO", "golang", "Golang", "GOLANG"],
                "Rust": ["rust", "RUST", "Rust语言"],
                "PHP": ["php", "PHP", "Php"],
                "Ruby": ["ruby", "RUBY", "Ruby语言"],
                "Swift": ["swift", "SWIFT", "Swift语言"],
                "Kotlin": ["kotlin", "KOTLIN", "Kotlin语言"],
                "Scala": ["scala", "SCALA"],
                "Shell": ["shell", "SHELL", "bash", "BASH", "Bash", "shell script"],
                "SQL": ["sql", "SQL", "Sql", "mysql", "MYSQL", "postgresql", "oracle sql"],
            }
        },
        "data_analysis": {
            "keywords": [
                "Tableau", "Power BI", "Origin", "SPSS", "SAS", "Stata", "Minitab",
                "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
                "Jupyter", "Anaconda", "RStudio", "Excel数据分析", "数据透视表"
            ],
            "display_name": "数据分析工具",
            "aliases": {
                "Tableau": ["tableau", "Tableau"],
                "Power BI": ["powerbi", "PowerBI", "power bi"],
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
                "AutoCAD", "3ds Max", "Maya", "Blender", "Cinema 4D", "Rhino",
                "PS", "PR", "AI", "AE", "LR", "AU", "CAD"
            ],
            "display_name": "设计软件",
            "aliases": {
                "Photoshop": ["photoshop", "PS", "ps", "Ps"],
                "Premiere": ["premiere", "PR", "pr", "Pr", "Premiere Pro"],
                "Illustrator": ["illustrator", "AI", "ai", "Ai"],
                "After Effects": ["after effects", "AE", "ae", "Ae"],
                "AutoCAD": ["autocad", "CAD", "cad", "Cad"],
            }
        },
        "frontend": {
            "keywords": [
                "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "jQuery",
                "Bootstrap", "Tailwind CSS", "HTML", "CSS", "Sass", "Less", "Webpack",
                "Vite", "Parcel", "Redux", "MobX", "Pinia", "Zustand", "jQuery UI",
                "Material-UI", "Ant Design", "Element UI", "Chakra UI", "Styled Components",
                "Emotion", "Styled-JSX", "CSS Modules", "PostCSS", "Babel", "ESLint",
                "Prettier", "Storybook", "Gatsby", "Gridsome", "Quasar", "Vuetify"
            ],
            "display_name": "前端技术",
            "aliases": {
                "React": ["react", "REACT", "React.js", "reactjs", "react.js"],
                "Vue": ["vue", "VUE", "Vue.js", "vuejs", "vue.js", "vue2", "vue3", "Vue2", "Vue3"],
                "Angular": ["angular", "ANGULAR", "Angular.js", "angularjs"],
                "Next.js": ["next.js", "nextjs", "NEXTJS", "NextJS", "next"],
                "Nuxt.js": ["nuxt.js", "nuxtjs", "NUXTJS", "NuxtJS", "nuxt"],
                "jQuery": ["jquery", "JQUERY", "JQuery"],
                "Bootstrap": ["bootstrap", "BOOTSTRAP"],
                "Tailwind CSS": ["tailwind", "tailwindcss", "TAILWIND", "tailwind css"],
                "HTML": ["html", "HTML5", "html5", "HTML 5"],
                "CSS": ["css", "CSS3", "css3", "CSS 3"],
                "Sass": ["sass", "SASS", "scss", "SCSS"],
                "Webpack": ["webpack", "WEBPACK"],
                "Redux": ["redux", "REDUX"],
            }
        },
        "backend": {
            "keywords": [
                "Node.js", "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "Express",
                "NestJS", "Laravel", "Rails", "ASP.NET", "gRPC", "GraphQL", "REST API",
                "Rocket", "Actix", "Tornado", "Koa", "ThinkPHP", "CodeIgniter", "Symfony",
                "Zend", "CakePHP", "Phoenix", "Echo", "Gin", "Beego", "Buffalo"
            ],
            "display_name": "后端框架",
            "aliases": {
                "Node.js": ["nodejs", "node.js", "NODEJS", "NodeJS", "node"],
                "Django": ["django", "DJANGO"],
                "Flask": ["flask", "FLASK"],
                "FastAPI": ["fastapi", "FASTAPI", "fast api"],
                "Spring": ["spring", "SPRING", "spring framework"],
                "Spring Boot": ["springboot", "spring boot", "SPRINGBOOT", "SpringBoot"],
                "Express": ["express", "EXPRESS", "express.js", "expressjs"],
                "NestJS": ["nestjs", "nest.js", "NESTJS", "Nestjs"],
                "GraphQL": ["graphql", "GRAPHQL", "graph ql"],
                "REST API": ["rest", "REST", "restful", "RESTFUL", "rest api", "REST API"],
            }
        },
        "databases": {
            "keywords": [
                "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
                "Oracle", "SQL Server", "Cassandra", "DynamoDB", "Firebase", "Neo4j",
                "ClickHouse", "InfluxDB", "TimescaleDB", "MariaDB", "CouchDB", "HBase",
                "BigQuery", "Snowflake", "Teradata", "DB2", "Sybase", "Access"
            ],
            "display_name": "数据库",
            "aliases": {
                "MySQL": ["mysql", "MYSQL", "MySql", "mysql数据库"],
                "PostgreSQL": ["postgresql", "POSTGRESQL", "postgres", "POSTGRES", "pgsql"],
                "MongoDB": ["mongodb", "MONGODB", "mongo", "MONGO", "mongo db"],
                "Redis": ["redis", "REDIS"],
                "Elasticsearch": ["elasticsearch", "ELASTICSEARCH", "es", "ES", "elastic search"],
                "SQLite": ["sqlite", "SQLITE", "sqlite3"],
                "Oracle": ["oracle", "ORACLE", "oracle数据库"],
                "SQL Server": ["sqlserver", "SQLSERVER", "sql server", "SQL SERVER", "mssql"],
            }
        },
        "ai_ml": {
            "keywords": [
                "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
                "Spark", "Hadoop", "Kafka", "Flink", "Airflow", "HBase", "Hive",
                "XGBoost", "LightGBM", "CatBoost", "OpenCV", "NLTK", "SpaCy",
                "Transformers", "BERT", "GPT", "LLM", "LangChain", "Pinecone", "Chroma",
                "Hugging Face", "ONNX", "TensorRT", "CUDA", "cuDNN", "MLflow", "Kubeflow"
            ],
            "display_name": "AI/大数据"
        },
        "devops": {
            "keywords": [
                "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", "Travis CI",
                "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云", "Heroku", "Vercel",
                "Linux", "Nginx", "Apache", "Git", "SVN", "Terraform", "Ansible",
                "Prometheus", "Grafana", "ELK", "Consul", "Vault", "Helm", "Istio",
                "CircleCI", "TeamCity", "Bamboo", "Puppet", "Chef", "SaltStack"
            ],
            "display_name": "DevOps/云"
        },
        "mobile": {
            "keywords": [
                "iOS", "Android", "React Native", "Flutter", "Swift", "Kotlin",
                "Xamarin", "Ionic", "Cordova", "PhoneGap", "uni-app", "Taro",
                "WeChat Mini Program", "支付宝小程序", "百度小程序", "快应用"
            ],
            "display_name": "移动端"
        },
        "testing": {
            "keywords": [
                "Jest", "Mocha", "Cypress", "Selenium", "Playwright", "Pytest",
                "JUnit", "TestNG", "Cucumber", "Appium", "Postman", "JMeter",
                "单元测试", "集成测试", "E2E测试", "自动化测试", "性能测试",
                "压力测试", "负载测试", "安全测试", "回归测试"
            ],
            "display_name": "测试"
        },
        "tools": {
            "keywords": [
                "VS Code", "IntelliJ IDEA", "PyCharm", "WebStorm", "Eclipse", "Xcode",
                "Jira", "Confluence", "Trello", "Notion", "Slack", "Teams",
                "Figma", "Sketch", "Photoshop", "Postman", "Charles", "Wireshark",
                "GitHub", "GitLab", "Bitbucket", "SourceTree", "Beyond Compare",
                "Navicat", "DataGrip", "Robo 3T", "Studio 3T", "MongoDB Compass"
            ],
            "display_name": "工具"
        },
        "methodologies": {
            "keywords": [
                "Microservices", "CI/CD", "Agile", "Scrum", "TDD", "DDD", "DevOps",
                "OOP", "Functional Programming", "Reactive Programming", "Event-Driven",
                "SOA", "MVC", "MVVM", "Clean Architecture", "Design Patterns",
                "AOP", "IOC", "DI", "RESTful", "Serverless", "BFF"
            ],
            "display_name": "方法论"
        },
        "languages": {
            "keywords": [
                "英语", "English", "中文", "Chinese", "日语", "Japanese", "法语", "French",
                "德语", "German", "西班牙语", "Spanish", "韩语", "Korean",
                "普通话", "粤语", "CET-4", "CET-6", "TEM-4", "TEM-8", "雅思", "托福",
                "GRE", "GMAT", "专四", "专八", "英语四级", "英语六级"
            ],
            "display_name": "语言能力"
        },
        "office": {
            "keywords": [
                "Microsoft Office", "Word", "Excel", "PowerPoint", "Access", "Outlook",
                "WPS", "金山办公", "Google Docs", "Google Sheets", "Google Slides",
                "Visio", "Project", "OneNote", "Teams", "SharePoint",
                "Office办公软件", "办公软件", "Office", "MS Office"
            ],
            "display_name": "办公软件",
            "aliases": {
                "Microsoft Office": ["Office", "MS Office", "office", "Office办公软件", "办公软件"],
                "Word": ["word", "WORD"],
                "Excel": ["excel", "EXCEL"],
                "PowerPoint": ["powerpoint", "PPT", "ppt", "Powerpoint"],
            }
        },
    })
    
    # 技能级别关键词 - 扩展版本
    skill_levels: Dict[str, List[str]] = field(default_factory=lambda: {
        "精通": [
            "精通", "expert", "master", "高级", "advanced", "非常熟悉", "熟练掌握",
            "精通掌握", "深入掌握", "精通使用", "专业级", "专家级"
        ],
        "熟练": [
            "熟练", "proficient", "熟悉", "familiar", "掌握", "skilled", "中级", "intermediate",
            "熟练使用", "熟悉使用", "能够使用", "具备", "具有", "掌握", "较好的"
        ],
        "入门": [
            "了解", "beginner", "入门", "basic", "初级", "接触过", "知道", "知晓",
            "基础", "基本", "简单了解", "略有了解", "接触过", "学习过"
        ],
    })
    
    # 技能分隔符 - 支持多种分隔符
    skill_separators: List[str] = field(default_factory=lambda: [
        '、', '，', ',', ';', '；', '|', '/', '·', ' ', '\n', '\t'
    ])


@dataclass
class QualityConfig:
    """质量评估配置"""
    # 关键字段清单
    critical_fields: List[str] = field(default_factory=lambda: [
        "personal_info.name",
        "personal_info.email",
        "personal_info.phone",
        "education",
        "work_experience",
        "skills",
    ])
    
    # 评分权重
    accuracy_weight: float = 0.5
    completeness_weight: float = 0.3
    confidence_weight: float = 0.2
    
    # 阈值
    min_acceptable_score: float = 0.7
    low_confidence_threshold: float = 0.5


# 全局配置实例
parser_config = ParserConfig()
ocr_config = OCRConfig()
layout_config = LayoutConfig()
extraction_config = ExtractionConfig()
skill_config = SkillConfig()
quality_config = QualityConfig()
