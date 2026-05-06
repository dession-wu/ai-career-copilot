import json
import re
import logging
import math
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class WeightedSkill:
    """加权技能数据模型"""
    name: str
    category: str  # core_tech, framework, tool, soft_skill
    weight: float
    found_in_jd: bool = False
    found_in_resume: bool = False
    confidence: float = 1.0  # 匹配置信度
    matched: bool = False


@dataclass
class DimensionScore:
    """维度得分数据模型"""
    dimension: str  # 维度名称
    score: float  # 得分 (0-100)
    weight: float  # 权重
    max_score: float = 100.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeightedMatchResult:
    """加权匹配结果数据模型"""
    overall_score: float  # 总体得分 (0-100)
    confidence: float  # 置信度 (0-1)
    dimension_scores: List[DimensionScore]  # 各维度得分
    skill_match: Dict[str, List[str]]  # 匹配和缺失的技能
    details: Dict[str, Any]  # 详细匹配信息
    processing_time_ms: float = 0.0  # 处理时间（毫秒）

# 关键词类别权重配置
CATEGORY_WEIGHTS = {
    "core_tech": 3.0,      # 编程语言、核心技术
    "framework": 2.5,      # 框架、库
    "tool": 1.5,           # 工具、平台
    "soft_skill": 2.0,     # 软技能
}

# 扩展关键词库 - 按类别组织
KEYWORD_CATEGORIES = {
    "core_tech": {
        "weight": 3.0,
        "keywords": [
            # 编程语言 - 主流
            "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Golang",
            "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Objective-C", "Scala", "Perl",
            "R", "MATLAB", "Lua", "Groovy", "Dart", "Elixir", "Erlang", "Haskell",
            "Clojure", "F#", "VB.NET", "Visual Basic", "Delphi", "Pascal", "Fortran",
            "COBOL", "Assembly", "ASM", "Shell", "Bash", "PowerShell", "Zsh",
            "SQL", "PL/SQL", "T-SQL", "NoSQL", "GraphQL", "HTML", "CSS", "Sass", "SCSS",
            "Less", "XML", "JSON", "YAML", "TOML", "Markdown", "LaTeX", "RegEx",
            # 编程语言 - 中文
            "Python语言", "Java语言", "C语言", "C加加", "C井", "Go语言", "Rust语言",
            "脚本语言", "面向对象", "函数式编程", "声明式编程", "命令式编程",
            # 核心技术概念
            "OOP", "面向对象编程", "Functional Programming", "Reactive Programming",
            "Event-Driven", "Aspect-Oriented", "Generic Programming", "Metaprogramming",
            "Concurrent Programming", "Parallel Programming", "Distributed Computing",
            "Multithreading", "Multiprocessing", "Async", "Asynchronous", "Synchronization",
            "Concurrency", "Parallelism", "Memory Management", "Garbage Collection",
            "Compiler", "Interpreter", "JIT", "AOT", "Bytecode", "Machine Code",
            "Algorithm", "Data Structure", "Design Pattern", "SOLID", "DRY", "KISS",
            "Big O", "Time Complexity", "Space Complexity", "Recursion", "Iteration",
            "Stack", "Queue", "Heap", "Tree", "Graph", "Hash Table", "Linked List",
            "Array", "Matrix", "String", "Binary Search", "Sorting", "Dynamic Programming",
            "Greedy Algorithm", "Backtracking", "Divide and Conquer", "Bit Manipulation",
            # 系统/底层
            "Operating System", "OS", "Linux", "Unix", "Windows", "macOS", "Kernel",
            "System Call", "Process", "Thread", "IPC", "Socket", "TCP/IP", "UDP",
            "HTTP", "HTTPS", "WebSocket", "gRPC", "REST", "RPC", "Network Protocol",
            "DNS", "CDN", "Load Balancer", "Reverse Proxy", "Firewall", "VPN",
            "SSL", "TLS", "Encryption", "Decryption", "Cryptography", "Security",
            "Authentication", "Authorization", "OAuth", "JWT", "SSO", "LDAP",
            "Virtualization", "Container", "VM", "Hypervisor", "KVM", "Xen",
            "Embedded", "Firmware", "IoT", "RTOS", "ARM", "x86", "RISC-V",
            # 数据库核心
            "Database", "DBMS", "RDBMS", "Relational Database", "ACID", "Transaction",
            "Index", "Query Optimization", "Normalization", "Denormalization",
            "Sharding", "Partitioning", "Replication", "Master-Slave", "Cluster",
            "Backup", "Recovery", "Migration", "ETL", "Data Warehouse", "Data Lake",
            "OLTP", "OLAP", "CAP Theorem", "BASE", "Eventual Consistency",
            # AI/ML核心
            "Artificial Intelligence", "AI", "Machine Learning", "ML", "Deep Learning",
            "Neural Network", "CNN", "RNN", "LSTM", "GRU", "Transformer", "Attention",
            "BERT", "GPT", "LLM", "Large Language Model", "NLP", "Computer Vision",
            "CV", "Reinforcement Learning", "Supervised Learning", "Unsupervised Learning",
            "Semi-Supervised Learning", "Self-Supervised Learning", "Transfer Learning",
            "Fine-tuning", "Prompt Engineering", "RAG", "Vector Database", "Embedding",
            "Classification", "Regression", "Clustering", "Dimensionality Reduction",
            "Feature Engineering", "Model Training", "Inference", "Deployment",
            "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
            "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "OpenCV",
            # 大数据核心
            "Big Data", "Hadoop", "Spark", "Flink", "Storm", "Kafka", "MapReduce",
            "HDFS", "YARN", "Hive", "HBase", "Cassandra", "Elasticsearch", "Logstash",
            "Kibana", "ELK", "ClickHouse", "Druid", "Presto", "Trino", "Airflow",
            # 云原生核心
            "Cloud Native", "Microservices", "Service Mesh", "Istio", "Envoy",
            "Serverless", "FaaS", "BaaS", "PaaS", "IaaS", "SaaS", "CaaS",
            "Kubernetes", "K8s", "Docker", "Containerd", "CRI-O", "Podman",
            "Helm", "Kustomize", "Operator", "CRD", "Ingress", "Service Discovery",
            "ConfigMap", "Secret", "Persistent Volume", "StatefulSet", "DaemonSet",
            "Job", "CronJob", "HPA", "VPA", "Cluster Autoscaler",
            # 前端核心
            "Frontend", "Backend", "Full Stack", "Web Development", "Mobile Development",
            "Responsive Design", "Progressive Web App", "PWA", "Single Page Application",
            "SPA", "Server-Side Rendering", "SSR", "Static Site Generation", "SSG",
            "Client-Side Rendering", "CSR", "Hydration", "Virtual DOM", "DOM",
            "Browser", "Web API", "Fetch API", "XHR", "AJAX", "CORS", "WebRTC",
            "WebAssembly", "WASM", "WebGL", "WebGPU", "Canvas", "SVG",
            # 移动端核心
            "iOS", "Android", "React Native", "Flutter", "SwiftUI", "Jetpack Compose",
            "Cordova", "Ionic", "PhoneGap", "Xamarin", "Unity", "Unreal Engine",
            "Mobile App", "Native App", "Hybrid App", "Cross-Platform",
            # DevOps核心
            "DevOps", "SRE", "Site Reliability Engineering", "CI/CD", "Continuous Integration",
            "Continuous Deployment", "Continuous Delivery", "GitOps", "Infrastructure as Code",
            "IaC", "Configuration Management", "Monitoring", "Observability", "Logging",
            "Tracing", "Metrics", "Alerting", "Incident Management", "Chaos Engineering",
            "Blue-Green Deployment", "Canary Deployment", "A/B Testing", "Feature Flag",
            # 测试核心
            "Testing", "Unit Test", "Integration Test", "E2E Test", "Regression Test",
            "Performance Test", "Load Test", "Stress Test", "Security Test", "Penetration Test",
            "TDD", "BDD", "Test Automation", "Mock", "Stub", "Spy", "Fixture",
            "Code Coverage", "Mutation Testing", "Static Analysis", "Linting",
            # 架构核心
            "System Design", "Architecture", "Monolithic", "Modular", "Layered Architecture",
            "MVC", "MVVM", "MVP", "Clean Architecture", "Hexagonal Architecture",
            "Domain-Driven Design", "DDD", "Event Sourcing", "CQRS", "Saga Pattern",
            "Circuit Breaker", "Bulkhead", "Retry", "Timeout", "Rate Limiting",
            "API Gateway", "BFF", "Backend for Frontend", "Message Queue", "Pub/Sub",
        ]
    },
    "framework": {
        "weight": 2.5,
        "keywords": [
            # Web框架 - Python
            "Django", "Flask", "FastAPI", "Tornado", "Bottle", "Pyramid", "Falcon",
            "Sanic", "Aiohttp", "Celery", "Django REST Framework", "DRF", "Flask-RESTful",
            "SQLAlchemy", "Peewee", "Tortoise ORM", "Pydantic", "Typer", "Click",
            # Web框架 - Java
            "Spring", "Spring Boot", "Spring MVC", "Spring Cloud", "Spring Security",
            "Spring Data", "Spring Batch", "Hibernate", "MyBatis", "JPA", "Jakarta EE",
            "Java EE", "Servlet", "JSP", "Thymeleaf", "Struts", "Play Framework",
            "Micronaut", "Quarkus", "Vert.x", "Netty",
            # Web框架 - JavaScript/TypeScript
            "React", "Vue", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Gatsby",
            "Svelte", "SvelteKit", "SolidJS", "Qwik", "Astro", "Remix", "RedwoodJS",
            "Express", "Express.js", "Koa", "Koa.js", "NestJS", "Nest.js", "Fastify",
            "Hapi", "Meteor", "Sails.js", "AdonisJS", "FeathersJS", "LoopBack",
            "Redux", "MobX", "Zustand", "Recoil", "Jotai", "Valtio", "Vuex", "Pinia",
            "React Router", "Vue Router", "React Query", "TanStack Query", "SWR",
            "Axios", "Fetch", "GraphQL", "Apollo", "Relay", "Urql", "Prisma",
            "TypeORM", "Sequelize", "Mongoose", "Knex", "Objection.js",
            "Webpack", "Vite", "Rollup", "Parcel", "esbuild", "Turbopack",
            "Babel", "SWC", "PostCSS", "Autoprefixer", "Tailwind CSS", "Bootstrap",
            "Material-UI", "MUI", "Ant Design", "Chakra UI", "Shadcn UI", "Radix UI",
            "Styled Components", "Emotion", "Sass", "Less", "Stylus",
            "Jest", "Mocha", "Chai", "Jasmine", "Cypress", "Playwright", "Puppeteer",
            "Testing Library", "Vitest", "Storybook", "Lerna", "Nx", "Turborepo",
            "Electron", "Tauri", "Capacitor", "Cordova",
            # Web框架 - PHP
            "Laravel", "Symfony", "CodeIgniter", "CakePHP", "Yii", "Zend Framework",
            "Laminas", "Slim", "Phalcon", "FuelPHP", "PHPixie",
            # Web框架 - Ruby
            "Ruby on Rails", "Rails", "Sinatra", "Hanami", "Padrino",
            # Web框架 - Go
            "Gin", "Echo", "Beego", "Revel", "Fiber", "Fasthttp", "Buffalo",
            "GORM", "sqlx",
            # Web框架 - Rust
            "Actix", "Axum", "Rocket", "Tide", "Warp", "Yew", "Leptos",
            # Web框架 - C#
            "ASP.NET", "ASP.NET Core", "ASP.NET MVC", "Web API", "Blazor", "WPF",
            "WinForms", "UWP", "Xamarin.Forms", "MAUI", "Entity Framework", "EF Core",
            "Dapper", "Nancy", "ServiceStack",
            # Web框架 - 其他
            "Phoenix", "Django CMS", "Wagtail", "Mezzanine", "WordPress", "Drupal",
            "Joomla", "Magento", "Shopify", "WooCommerce", "Laravel Nova",
            # 移动端框架
            "React Native", "Flutter", "Ionic", "Cordova", "Capacitor", "NativeScript",
            "SwiftUI", "Jetpack Compose", "UIKit", "Android SDK", "Xamarin",
            "Unity", "Unreal Engine", "Godot", "Cocos2d", "Phaser",
            # AI/ML框架
            "TensorFlow", "PyTorch", "Keras", "JAX", "Flax", "Haiku", "MXNet",
            "Caffe", "Caffe2", "Theano", "PaddlePaddle", "MindSpore", "ONNX",
            "Hugging Face", "Transformers", "Tokenizers", "Datasets", "Accelerate",
            "LangChain", "LlamaIndex", "AutoGPT", "LangGraph", "CrewAI",
            "OpenAI API", "Anthropic API", "Gemini API", "Cohere", "Mistral AI",
            "Scikit-learn", "XGBoost", "LightGBM", "CatBoost", "Optuna", "Ray",
            "MLflow", "Kubeflow", "Weights & Biases", "WandB", "TensorBoard",
            "OpenCV", "PIL", "Pillow", "scikit-image", "Albumentations",
            "NLTK", "spaCy", "Gensim", "TextBlob", "Stanza", "CoreNLP",
            "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
            "Bokeh", "Altair", "ggplot", "D3.js", "ECharts", "Highcharts",
            # 大数据框架
            "Apache Spark", "Apache Flink", "Apache Storm", "Apache Kafka",
            "Apache Hadoop", "Apache Hive", "Apache HBase", "Apache Cassandra",
            "Apache Druid", "Apache Pinot", "Apache Pulsar", "Apache Beam",
            "Delta Lake", "Apache Iceberg", "Apache Hudi", "Databricks",
            "Snowflake", "BigQuery", "Redshift", "Athena", "Presto", "Trino",
            # 云原生框架
            "Kubernetes", "K8s", "Docker", "containerd", "CRI-O", "Podman",
            "Helm", "Kustomize", "Terraform", "Pulumi", "Ansible", "Puppet",
            "Chef", "SaltStack", "Vagrant", "Packer", "Consul", "Vault",
            "Nomad", "Envoy", "Istio", "Linkerd", "Consul Connect", "Traefik",
            "NGINX", "Apache HTTP Server", "HAProxy", "Caddy",
            "Prometheus", "Grafana", "ELK Stack", "Fluentd", "Jaeger", "Zipkin",
            "ArgoCD", "Flux", "Spinnaker", "Jenkins", "GitLab CI", "GitHub Actions",
            "CircleCI", "Travis CI", "Drone CI", "Tekton", "Buildkite",
            # 测试框架
            "JUnit", "TestNG", "Mockito", "PowerMock", "Cucumber", "Selenium",
            "Appium", "Robot Framework", "PyTest", "Unittest", "Doctest",
            "RSpec", "Capybara", "Minitest", "PHPUnit", "Codeception", "Behat",
            "Jest", "Mocha", "Chai", "Cypress", "Playwright", "Puppeteer",
            "Karma", "Jasmine", "Protractor", "Nightwatch", "WebdriverIO",
            "Artillery", "k6", "Locust", "JMeter", "Gatling", "Tsung",
            # 安全框架
            "Spring Security", "Shiro", "OAuth2", "OpenID Connect", "Keycloak",
            "Auth0", "Okta", "Firebase Auth", "AWS Cognito", "Azure AD",
            "HashiCorp Vault", "Cert-Manager", "Let's Encrypt",
            # ORM/数据库框架
            "Hibernate", "MyBatis", "JPA", "Entity Framework", "Dapper",
            "SQLAlchemy", "Peewee", "Tortoise ORM", "Prisma", "TypeORM",
            "Sequelize", "Mongoose", "Knex", "Objection.js", "Bookshelf",
            "Active Record", "DataMapper", "Doctrine", "Eloquent",
            # 消息队列框架
            "RabbitMQ", "Apache Kafka", "Apache Pulsar", "ActiveMQ", "RocketMQ",
            "ZeroMQ", "NATS", "Redis Pub/Sub", "AWS SQS", "AWS SNS",
            "Google Pub/Sub", "Azure Service Bus", "Azure Event Hubs",
            # 缓存框架
            "Redis", "Memcached", "Hazelcast", "Ehcache", "Caffeine",
            "Guava Cache", "Spring Cache", "Cache2k", "Ignite",
            # 搜索引擎框架
            "Elasticsearch", "Apache Solr", "Apache Lucene", "Meilisearch",
            "Typesense", "Algolia", "Sphinx", "Xunsearch",
            # 任务调度框架
            "Quartz", "Spring Scheduler", "Celery", "APScheduler", "Hangfire",
            "Sidekiq", "Resque", "Delayed Job", "Bull", "Agenda",
            "Airflow", "Prefect", "Dagster", "Luigi", "Cronicle",
        ]
    },
    "tool": {
        "weight": 1.5,
        "keywords": [
            # 版本控制
            "Git", "SVN", "Mercurial", "Perforce", "GitHub", "GitLab", "Bitbucket",
            "Gitea", "Gogs", "SourceForge", "GitKraken", "Sourcetree", "TortoiseGit",
            "GitHub Desktop", "Fork", "Tower", "Git Extensions",
            # IDE/编辑器
            "VS Code", "Visual Studio Code", "IntelliJ IDEA", "PyCharm", "WebStorm",
            "PhpStorm", "Rider", "CLion", "GoLand", "RubyMine", "DataGrip",
            "Visual Studio", "VS", "Eclipse", "NetBeans", "Android Studio", "Xcode",
            "Sublime Text", "Atom", "Vim", "Neovim", "Emacs", "Notepad++",
            "Cursor", "Windsurf", "Trae", "Zed", "Fleet",
            # 数据库工具
            "MySQL", "PostgreSQL", "SQLite", "MariaDB", "Oracle", "SQL Server",
            "MongoDB", "Redis", "Cassandra", "Couchbase", "CouchDB", "Neo4j",
            "DynamoDB", "Firestore", "Cosmos DB", "Bigtable", "Spanner",
            "MySQL Workbench", "pgAdmin", "DBeaver", "Navicat", "DataGrip",
            "TablePlus", "Sequel Pro", "Robo 3T", "MongoDB Compass", "Redis Desktop Manager",
            "phpMyAdmin", "Adminer", "pgweb", "OmniDB",
            # API工具
            "Postman", "Insomnia", "Hoppscotch", "Swagger", "OpenAPI", "API Blueprint",
            "GraphiQL", "GraphQL Playground", "Altair", "HTTPie", "cURL", "wget",
            # 云平台
            "AWS", "Amazon Web Services", "EC2", "S3", "Lambda", "RDS", "ECS", "EKS",
            "Azure", "Microsoft Azure", "Azure VM", "Azure Storage", "Azure Functions",
            "GCP", "Google Cloud Platform", "Compute Engine", "Cloud Storage", "Cloud Functions",
            "阿里云", "腾讯云", "华为云", "百度云", "京东云", "UCloud", "青云",
            "DigitalOcean", "Linode", "Vultr", "Heroku", "Netlify", "Vercel",
            "Cloudflare", "Fastly", "AWS CloudFront", "Firebase", "Supabase",
            "Terraform Cloud", "Pulumi Cloud", "Ansible Tower", "AWX",
            # 容器/编排工具
            "Docker", "Docker Compose", "Docker Swarm", "Kubernetes", "K8s",
            "kubectl", "Helm", "Kustomize", "Skaffold", "Tilt", "DevSpace",
            "Rancher", "OpenShift", "K3s", "MicroK8s", "Minikube", "Kind",
            "Portainer", "Rancher Desktop", "Docker Desktop", "Podman Desktop",
            # CI/CD工具
            "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
            "Drone", "Tekton", "ArgoCD", "Flux", "Spinnaker", "Buildkite",
            "TeamCity", "Bamboo", "Azure DevOps", "AWS CodePipeline", "Google Cloud Build",
            # 监控/日志工具
            "Prometheus", "Grafana", "ELK Stack", "EFK Stack", "Datadog",
            "New Relic", "Splunk", "AppDynamics", "Dynatrace", "Instana",
            "Sentry", "Bugsnag", "Rollbar", "Airbrake", "LogRocket",
            "Fluentd", "Fluent Bit", "Logstash", "Filebeat", "Metricbeat",
            "Jaeger", "Zipkin", "Tempo", "SkyWalking", "Pinpoint",
            "PagerDuty", "Opsgenie", "VictorOps", "Alertmanager",
            # 协作工具
            "Jira", "Confluence", "Trello", "Asana", "Monday", "Notion",
            "Linear", "ClickUp", "Wrike", "Basecamp", "Redmine", "YouTrack",
            "Slack", "Microsoft Teams", "Discord", "Zoom", "Google Meet",
            "Figma", "Sketch", "Adobe XD", "InVision", "Zeplin", "Abstract",
            "Miro", "Mural", "Lucidchart", "Draw.io", "diagrams.net",
            # 文档工具
            "Swagger UI", "ReDoc", "GitBook", "ReadMe", "Docusaurus", "VuePress",
            "MkDocs", "Sphinx", "Javadoc", "TypeDoc", "ESDoc", "Compodoc",
            "Markdown", "MDX", "AsciiDoc", "reStructuredText",
            # 设计工具
            "Photoshop", "Illustrator", "Premiere", "After Effects", "Figma",
            "Sketch", "Adobe XD", "InVision", "Axure", "Balsamiq", "Proto.io",
            "Canva", "Crello", "Gravit Designer", "Affinity Designer",
            "Blender", "Maya", "3ds Max", "Cinema 4D", "ZBrush",
            # 测试工具
            "Selenium", "Cypress", "Playwright", "Puppeteer", "Appium",
            "Postman", "SoapUI", "Katalon", "TestComplete", "Ranorex",
            "SonarQube", "ESLint", "Prettier", "TSLint", "Stylelint",
            "Black", "Flake8", "Pylint", "Mypy", "Bandit", "Safety",
            # 安全工具
            "Burp Suite", "OWASP ZAP", "Nmap", "Metasploit", "Wireshark",
            "Nessus", "Qualys", "Acunetix", "Checkmarx", "Veracode",
            "Snyk", "Dependabot", "WhiteSource", "Black Duck", "FOSSA",
            # 性能工具
            "JMeter", "Gatling", "Locust", "k6", "Artillery", "Tsung",
            "LoadRunner", "NeoLoad", "WebLOAD", "LoadNinja",
            "Chrome DevTools", "Lighthouse", "WebPageTest", "GTmetrix",
            "Blackfire", "XHProf", "Tideways", "New Relic APM",
            # 构建工具
            "Maven", "Gradle", "Ant", "MSBuild", "CMake", "Make", "Ninja",
            "Webpack", "Vite", "Rollup", "Parcel", "esbuild", "Turbopack",
            "Babel", "SWC", "TypeScript Compiler", "tsc",
            # 包管理工具
            "npm", "yarn", "pnpm", "bun", "pip", "conda", "poetry",
            "pipenv", "virtualenv", "venv", "requirements.txt", "pyproject.toml",
            "Maven Central", "Gradle Plugin", "NuGet", "Chocolatey", "Homebrew",
            "apt", "yum", "dnf", "pacman", "brew", "snap", "flatpak",
            # 虚拟化工具
            "VMware", "VirtualBox", "Hyper-V", "KVM", "Xen", "QEMU",
            "Parallels", "Virtual PC", "UTM", "Multipass", "LXD",
            # 终端/Shell工具
            "Terminal", "iTerm2", "Windows Terminal", "ConEmu", "Cmder",
            "tmux", "screen", "byobu", "zellij", "guake", "yakuake",
            "Oh My Zsh", "Powerlevel10k", "Starship", "Fish Shell",
            "PowerShell", "Bash", "Zsh", "Fish", "Oh My Bash",
            # 其他开发工具
            "Charles", "Fiddler", "Wireshark", "tcpdump", "ngrep",
            "Postman", "Insomnia", "HTTPie", "cURL", "wget",
            "ngrok", "localtunnel", "serveo", "Pagekite",
            "Frp", "NPS", "Rathole", "Cloudflare Tunnel",
        ]
    },
    "soft_skill": {
        "weight": 2.0,
        "keywords": [
            # 沟通能力
            "Communication", "沟通", "表达能力", "Presentation", "演讲",
            "Public Speaking", "Public Speaking", "Written Communication", "写作",
            "Active Listening", "倾听", "Feedback", "反馈", "Negotiation", "谈判",
            "Persuasion", "说服", "Storytelling", "讲故事", "Technical Writing", "技术写作",
            "Documentation", "文档编写", "Meeting Facilitation", "会议主持",
            "Cross-functional Communication", "跨部门沟通", "Stakeholder Management", "利益相关者管理",
            # 团队协作
            "Teamwork", "团队合作", "Collaboration", "协作", "Cooperation", "配合",
            "Team Building", "团队建设", "Conflict Resolution", "冲突解决",
            "Interpersonal Skills", "人际交往", "Relationship Building", "关系建立",
            "Peer Review", "同行评审", "Pair Programming", "结对编程", "Mob Programming",
            "Knowledge Sharing", "知识分享", "Mentoring", "指导", "Coaching", "辅导",
            "Onboarding", "新人培训", "Team Leadership", "团队领导",
            # 领导力
            "Leadership", "领导力", "Management", "管理", "People Management", "人员管理",
            "Project Management", "项目管理", "Program Management", "项目集管理",
            "Product Management", "产品经理", "Technical Leadership", "技术领导",
            "Engineering Management", "工程管理", "Team Lead", "Tech Lead",
            "CTO", "技术总监", "VP of Engineering", "工程副总裁",
            "Decision Making", "决策", "Delegation", "授权", "Empowerment", "赋能",
            "Vision", "愿景", "Strategy", "战略", "Roadmap", "路线图",
            # 问题解决
            "Problem Solving", "问题解决", "Critical Thinking", "批判性思维",
            "Analytical Thinking", "分析思维", "Logical Thinking", "逻辑思维",
            "Creative Thinking", "创造性思维", "Innovation", "创新",
            "Troubleshooting", "故障排查", "Debugging", "调试", "Root Cause Analysis", "根因分析",
            "Decision Analysis", "决策分析", "Risk Assessment", "风险评估",
            "Incident Management", "事件管理", "Crisis Management", "危机管理",
            # 学习能力
            "Learning Ability", "学习能力", "Self-Learning", "自学",
            "Continuous Learning", "持续学习", "Lifelong Learning", "终身学习",
            "Adaptability", "适应性", "Flexibility", "灵活性", "Resilience", "韧性",
            "Growth Mindset", "成长型思维", "Curiosity", "好奇心", "Open-mindedness", "开放心态",
            "Research", "研究", "Exploration", "探索", "Experimentation", "实验",
            "Skill Acquisition", "技能获取", "Upskilling", "技能提升", "Reskilling", "技能重塑",
            # 时间管理
            "Time Management", "时间管理", "Prioritization", "优先级管理",
            "Task Management", "任务管理", "Scheduling", "日程安排",
            "Deadline Management", "截止期限管理", "Multitasking", "多任务处理",
            "Work-Life Balance", "工作生活平衡", "Focus", "专注力", "Concentration", "集中注意力",
            "Productivity", "生产力", "Efficiency", "效率", "Effectiveness", "效能",
            "Agile", "敏捷", "Scrum", "Kanban", "Sprint", "迭代",
            # 责任心
            "Responsibility", "责任心", "Accountability", "问责制", "Ownership", "主人翁意识",
            "Commitment", "承诺", "Dedication", "奉献", "Reliability", "可靠性",
            "Professionalism", "专业精神", "Work Ethic", "职业道德", "Integrity", "诚信",
            "Attention to Detail", "注重细节", "Thoroughness", "彻底性", "Accuracy", "准确性",
            "Quality Focus", "质量导向", "Excellence", "卓越", "Perfectionism", "完美主义",
            # 抗压能力
            "Stress Management", "压力管理", "Pressure Handling", "压力处理",
            "Emotional Intelligence", "情商", "EQ", "Self-Awareness", "自我意识",
            "Self-Regulation", "自我调节", "Motivation", "动机", "Self-Motivation", "自我激励",
            "Patience", "耐心", "Perseverance", "毅力", "Persistence", "坚持",
            "Grit", "坚毅", "Endurance", "耐力", "Stamina", "持久力",
            "Work Under Pressure", "抗压能力", "Tight Deadline", "紧急期限",
            # 商业意识
            "Business Acumen", "商业敏锐度", "Business Understanding", "业务理解",
            "Domain Knowledge", "领域知识", "Industry Knowledge", "行业知识",
            "Customer Focus", "客户导向", "User-Centric", "用户中心",
            "Product Thinking", "产品思维", "Design Thinking", "设计思维",
            "Data-Driven", "数据驱动", "Metrics-Driven", "指标驱动", "KPI", "OKR",
            "ROI", "投资回报率", "Cost-Benefit Analysis", "成本效益分析",
            "Market Analysis", "市场分析", "Competitive Analysis", "竞争分析",
            "Strategic Thinking", "战略思维", "Systems Thinking", "系统思维",
            # 其他软技能
            "Initiative", "主动性", "Proactivity", "积极性", "Entrepreneurship", "创业精神",
            "Creativity", "创造力", "Resourcefulness", "足智多谋", "Versatility", "多才多艺",
            "Cultural Awareness", "文化意识", "Diversity", "多元化", "Inclusion", "包容性",
            "Ethics", "伦理", "Compliance", "合规", "Governance", "治理",
            "Change Management", "变革管理", "Transformation", "转型", "Digital Transformation", "数字化转型",
            "Remote Work", "远程工作", "Distributed Teams", "分布式团队", "Async Communication", "异步沟通",
            "Open Source Contribution", "开源贡献", "Community Building", "社区建设",
            "Public Relations", "公共关系", "Marketing", "市场营销", "Sales", "销售",
            "Customer Service", "客户服务", "Support", "技术支持", "Consulting", "咨询",
        ]
    },
}

# 构建总关键词列表（向后兼容）
ALL_KEYWORDS = []
for category in KEYWORD_CATEGORIES.values():
    ALL_KEYWORDS.extend(category["keywords"])

# 去重
ALL_KEYWORDS = list(set(ALL_KEYWORDS))

# 同义词映射表：将常见缩写/别名映射到标准名称
SYNONYM_MAP = {
    # JavaScript 生态
    "js": "javascript",
    "ts": "typescript",
    "node": "nodejs",
    "node.js": "nodejs",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "nextjs": "next",
    "next.js": "next",
    "nuxtjs": "nuxt",
    "nuxt.js": "nuxt",
    "expressjs": "express",
    "express.js": "express",
    "nestjs": "nestjs",
    "nest.js": "nestjs",
    # Python 生态
    "py": "python",
    "py3": "python",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    # Go 生态
    "golang": "go",
    # 容器与云原生
    "k8s": "kubernetes",
    "docker": "docker",
    # 数据库
    "postgres": "postgresql",
    "mongo": "mongodb",
    "es": "elasticsearch",
    "redis": "redis",
    # 云服务
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure",
    # AI/ML
    "tf": "tensorflow",
    "pytorch": "pytorch",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "nlp",
    "cv": "computer vision",
    # 其他
    "kubenetes": "kubernetes",  # 常见拼写错误
    "postgre": "postgresql",
    "tailwind": "tailwindcss",
    "tailwind css": "tailwindcss",
}


def normalize_keyword(keyword: str) -> str:
    """
    标准化关键词：将同义词/缩写映射为标准名称

    Args:
        keyword: 原始关键词

    Returns:
        标准化后的关键词
    """
    if not keyword:
        return keyword

    # 转换为小写进行匹配
    keyword_lower = keyword.lower().strip()

    # 直接匹配
    if keyword_lower in SYNONYM_MAP:
        return SYNONYM_MAP[keyword_lower]

    # 处理带点的变体（如 react.js -> react）
    keyword_no_dot = keyword_lower.replace(".", "")
    if keyword_no_dot in SYNONYM_MAP:
        return SYNONYM_MAP[keyword_no_dot]

    # 处理带空格的变体（如 "tailwind css" -> "tailwindcss"）
    keyword_no_space = keyword_lower.replace(" ", "")
    if keyword_no_space in SYNONYM_MAP:
        return SYNONYM_MAP[keyword_no_space]

    # 返回原始关键词（首字母大写格式）
    return keyword


class LLMService:
    def __init__(self, db: Session = None):
        self.db = db

    # 动态权重配置 - 根据岗位类型调整
    DYNAMIC_WEIGHT_CONFIGS = {
        "backend": {
            "name": "后端开发",
            "description": "后端开发岗位",
            "weights": {
                "core_tech": 4.0,      # 核心技术权重最高
                "framework": 3.5,      # 框架次之
                "tool": 1.5,
                "soft_skill": 1.5,
            },
            "keywords": ["后端", "backend", "server", "api", "database", "服务器"]
        },
        "frontend": {
            "name": "前端开发",
            "description": "前端开发岗位",
            "weights": {
                "core_tech": 3.5,
                "framework": 4.0,      # 前端框架权重最高
                "tool": 2.0,
                "soft_skill": 1.5,
            },
            "keywords": ["前端", "frontend", "web", "ui", "界面", "css", "html"]
        },
        "ai_engineer": {
            "name": "AI/算法工程师",
            "description": "AI和算法相关岗位",
            "weights": {
                "core_tech": 4.5,      # 核心技术权重最高
                "framework": 2.5,
                "tool": 1.5,
                "soft_skill": 1.5,
            },
            "keywords": ["ai", "算法", "机器学习", "深度学习", "machine learning", "deep learning", "nlp", "cv"]
        },
        "data_engineer": {
            "name": "数据工程师",
            "description": "数据工程相关岗位",
            "weights": {
                "core_tech": 3.5,
                "framework": 2.5,
                "tool": 3.5,           # 数据工具权重较高
                "soft_skill": 1.5,
            },
            "keywords": ["数据", "data", "etl", "pipeline", "warehouse", "大数据"]
        },
        "devops": {
            "name": "DevOps工程师",
            "description": "DevOps和运维相关岗位",
            "weights": {
                "core_tech": 3.0,
                "framework": 2.0,
                "tool": 4.0,           # 工具权重最高
                "soft_skill": 2.0,
            },
            "keywords": ["devops", "运维", "sre", "kubernetes", "docker", "ci/cd", "cloud"]
        },
        "fullstack": {
            "name": "全栈开发",
            "description": "全栈开发岗位",
            "weights": {
                "core_tech": 3.5,
                "framework": 3.5,
                "tool": 1.5,
                "soft_skill": 2.0,     # 软技能权重略高
            },
            "keywords": ["全栈", "fullstack", "full-stack", "前后端"]
        },
        "mobile": {
            "name": "移动端开发",
            "description": "移动端开发岗位",
            "weights": {
                "core_tech": 3.5,
                "framework": 4.0,      # 移动端框架权重高
                "tool": 1.5,
                "soft_skill": 1.5,
            },
            "keywords": ["移动端", "mobile", "ios", "android", "app", "flutter", "react native"]
        },
        "default": {
            "name": "通用",
            "description": "默认配置",
            "weights": {
                "core_tech": 3.0,
                "framework": 2.5,
                "tool": 1.5,
                "soft_skill": 2.0,
            },
            "keywords": []
        }
    }

    def _detect_job_type(self, jd_text: str) -> str:
        """
        根据JD文本检测岗位类型

        Args:
            jd_text: 职位描述文本

        Returns:
            str: 岗位类型标识符
        """
        jd_text_lower = jd_text.lower()
        scores = {}

        for job_type, config in self.DYNAMIC_WEIGHT_CONFIGS.items():
            if job_type == "default":
                continue

            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in jd_text_lower:
                    score += 1
            scores[job_type] = score

        # 返回得分最高的岗位类型
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return best_match

        return "default"

    def _get_dynamic_weights(self, job_type: str) -> Dict[str, float]:
        """
        获取指定岗位类型的动态权重配置

        Args:
            job_type: 岗位类型标识符

        Returns:
            Dict[str, float]: 权重配置
        """
        config = self.DYNAMIC_WEIGHT_CONFIGS.get(job_type, self.DYNAMIC_WEIGHT_CONFIGS["default"])
        return config["weights"]

    def _get_llm_client(self, llm_config: Optional[Dict[str, Any]] = None):
        """获取 LLM 客户端，支持多种 provider"""
        if not llm_config:
            return None

        api_key = llm_config.get("api_key")
        base_url = llm_config.get("base_url")
        model = llm_config.get("model", "gpt-3.5-turbo")

        if not api_key:
            return None

        try:
            from langchain_openai import ChatOpenAI

            client = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url if base_url else None,
                temperature=0.7,
            )
            return client
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            return None

    def _extract_keywords(self, text: str) -> List[str]:
        """
        基础 NLP：从文本中提取关键词（使用扩展关键词库）

        使用全局 ALL_KEYWORDS 列表进行匹配，支持 500+ 技术关键词
        """
        found_keywords = set()
        text_upper = text.upper()

        # 使用扩展的关键词库进行匹配
        for keyword in ALL_KEYWORDS:
            # 简单的子串匹配（不区分大小写）
            if keyword.upper() in text_upper:
                found_keywords.add(keyword)

        return list(found_keywords)

    def _extract_keywords_with_weights(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取关键词并返回带权重的结果

        Returns:
            Dict: {
                "keywords": List[str],  # 所有找到的关键词
                "by_category": Dict[str, List[str]],  # 按类别分组的关键词
                "weighted_score": float,  # 加权分数
                "category_scores": Dict[str, float]  # 各类别得分
            }
        """
        text_upper = text.upper()
        found_keywords = []
        by_category = {}
        category_scores = {}

        # 按类别提取关键词
        for category_name, category_data in KEYWORD_CATEGORIES.items():
            category_keywords = []
            weight = category_data["weight"]

            for keyword in category_data["keywords"]:
                if keyword.upper() in text_upper:
                    category_keywords.append(keyword)
                    found_keywords.append(keyword)

            by_category[category_name] = category_keywords
            category_scores[category_name] = len(category_keywords) * weight

        # 计算加权总分
        weighted_score = sum(category_scores.values())

        return {
            "keywords": list(set(found_keywords)),  # 去重
            "by_category": by_category,
            "weighted_score": round(weighted_score, 2),
            "category_scores": {k: round(v, 2) for k, v in category_scores.items()}
        }

    def _calculate_weighted_match_score(
        self,
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算加权匹配度分数

        Returns:
            Dict: 包含分数和详细匹配信息
        """
        jd_by_category = jd_keywords_result.get("by_category", {})
        resume_by_category = resume_keywords_result.get("by_category", {})

        category_matches = {}
        total_weighted_matched = 0
        total_weighted_jd = 0

        for category_name, category_data in KEYWORD_CATEGORIES.items():
            weight = category_data["weight"]
            jd_keywords = set(jd_by_category.get(category_name, []))
            resume_keywords = set(resume_by_category.get(category_name, []))

            matched = jd_keywords & resume_keywords
            missing = jd_keywords - resume_keywords

            category_weighted_matched = len(matched) * weight
            category_weighted_total = len(jd_keywords) * weight

            category_matches[category_name] = {
                "matched": list(matched),
                "missing": list(missing),
                "match_count": len(matched),
                "total_count": len(jd_keywords),
                "category_score": round((len(matched) / len(jd_keywords) * 100) if jd_keywords else 0, 2)
            }

            total_weighted_matched += category_weighted_matched
            total_weighted_jd += category_weighted_total

        # 计算总体加权分数
        overall_score = int((total_weighted_matched / total_weighted_jd * 100) if total_weighted_jd > 0 else 0)

        return {
            "overall_score": min(overall_score, 100),
            "category_matches": category_matches,
            "weighted_details": {
                "total_weighted_matched": round(total_weighted_matched, 2),
                "total_weighted_jd": round(total_weighted_jd, 2)
            }
        }

    def calculate_weighted_score(
        self,
        jd_text: str,
        resume_text: str,
        use_dynamic_weights: bool = True
    ) -> WeightedMatchResult:
        """
        计算加权匹配分数（带置信度）

        Args:
            jd_text: 职位描述文本
            resume_text: 简历文本
            use_dynamic_weights: 是否使用动态权重（根据岗位类型调整）

        Returns:
            WeightedMatchResult: 包含分数、置信度和详细匹配信息
        """
        import time
        start_time = time.time()

        # 0. 检测岗位类型并获取动态权重
        job_type = self._detect_job_type(jd_text) if use_dynamic_weights else "default"
        dynamic_weights = self._get_dynamic_weights(job_type)

        # 1. 提取带权重的关键词
        jd_keywords_result = self._extract_keywords_with_weights(jd_text)
        resume_keywords_result = self._extract_keywords_with_weights(resume_text)

        # 2. 构建技能列表（使用动态权重）
        weighted_skills = self._build_weighted_skills_with_dynamic_weights(
            jd_keywords_result,
            resume_keywords_result,
            dynamic_weights
        )

        # 3. 计算各维度得分（使用动态权重）
        dimension_scores = self._calculate_dimension_scores_with_dynamic_weights(
            weighted_skills,
            jd_keywords_result,
            resume_keywords_result,
            dynamic_weights
        )

        # 4. 计算总体得分
        overall_score = self._calculate_overall_score_with_dynamic_weights(
            dimension_scores,
            dynamic_weights
        )

        # 5. 计算置信度
        confidence = self._calculate_confidence(
            weighted_skills,
            jd_keywords_result,
            resume_keywords_result
        )

        # 6. 构建技能匹配结果
        skill_match = self._build_skill_match_result(weighted_skills)

        # 7. 构建详细信息
        details = self._build_match_details(
            weighted_skills,
            dimension_scores,
            jd_keywords_result,
            resume_keywords_result
        )

        # 添加岗位类型信息
        details["job_type"] = {
            "type": job_type,
            "name": self.DYNAMIC_WEIGHT_CONFIGS.get(job_type, {}).get("name", "通用"),
            "weights_used": dynamic_weights
        }

        processing_time_ms = (time.time() - start_time) * 1000

        return WeightedMatchResult(
            overall_score=round(overall_score, 2),
            confidence=round(confidence, 4),
            dimension_scores=dimension_scores,
            skill_match=skill_match,
            details=details,
            processing_time_ms=round(processing_time_ms, 2)
        )

    def _build_weighted_skills(
        self,
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any]
    ) -> List[WeightedSkill]:
        """构建加权技能列表"""
        weighted_skills = []
        jd_by_category = jd_keywords_result.get("by_category", {})
        resume_by_category = resume_keywords_result.get("by_category", {})

        # 收集所有类别中的所有技能
        all_categories = set(jd_by_category.keys()) | set(resume_by_category.keys())

        for category in all_categories:
            category_weight = KEYWORD_CATEGORIES.get(category, {}).get("weight", 1.0)
            jd_skills = set(jd_by_category.get(category, []))
            resume_skills = set(resume_by_category.get(category, []))
            all_skills = jd_skills | resume_skills

            for skill in all_skills:
                found_in_jd = skill in jd_skills
                found_in_resume = skill in resume_skills
                matched = found_in_jd and found_in_resume

                # 计算单个技能的置信度
                confidence = self._calculate_skill_confidence(
                    skill, category, found_in_jd, found_in_resume
                )

                weighted_skills.append(WeightedSkill(
                    name=skill,
                    category=category,
                    weight=category_weight,
                    found_in_jd=found_in_jd,
                    found_in_resume=found_in_resume,
                    confidence=confidence,
                    matched=matched
                ))

        return weighted_skills

    def _build_weighted_skills_with_dynamic_weights(
        self,
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any],
        dynamic_weights: Dict[str, float]
    ) -> List[WeightedSkill]:
        """构建加权技能列表（使用动态权重）"""
        weighted_skills = []
        jd_by_category = jd_keywords_result.get("by_category", {})
        resume_by_category = resume_keywords_result.get("by_category", {})

        # 收集所有类别中的所有技能
        all_categories = set(jd_by_category.keys()) | set(resume_by_category.keys())

        for category in all_categories:
            # 使用动态权重
            category_weight = dynamic_weights.get(category, KEYWORD_CATEGORIES.get(category, {}).get("weight", 1.0))
            jd_skills = set(jd_by_category.get(category, []))
            resume_skills = set(resume_by_category.get(category, []))
            all_skills = jd_skills | resume_skills

            for skill in all_skills:
                found_in_jd = skill in jd_skills
                found_in_resume = skill in resume_skills
                matched = found_in_jd and found_in_resume

                # 计算单个技能的置信度
                confidence = self._calculate_skill_confidence(
                    skill, category, found_in_jd, found_in_resume
                )

                weighted_skills.append(WeightedSkill(
                    name=skill,
                    category=category,
                    weight=category_weight,
                    found_in_jd=found_in_jd,
                    found_in_resume=found_in_resume,
                    confidence=confidence,
                    matched=matched
                ))

        return weighted_skills

    def _calculate_dimension_scores_with_dynamic_weights(
        self,
        weighted_skills: List[WeightedSkill],
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any],
        dynamic_weights: Dict[str, float]
    ) -> List[DimensionScore]:
        """计算各维度得分（使用动态权重）"""
        dimension_scores = []
        jd_by_category = jd_keywords_result.get("by_category", {})

        for category_name in dynamic_weights.keys():
            weight = dynamic_weights.get(category_name, 1.0)
            jd_skills = set(jd_by_category.get(category_name, []))

            # 获取该类别的技能
            category_skills = [s for s in weighted_skills if s.category == category_name]

            if not jd_skills:
                # JD中没有该类别的技能要求
                dimension_scores.append(DimensionScore(
                    dimension=category_name,
                    score=100.0,  # 默认满分
                    weight=weight,
                    details={"reason": "JD中无此类别要求"}
                ))
                continue

            # 计算匹配数
            matched_count = sum(1 for s in category_skills if s.matched)
            total_count = len(jd_skills)

            # 计算得分
            score = (matched_count / total_count * 100) if total_count > 0 else 0

            # 加权得分
            weighted_score = score * weight

            dimension_scores.append(DimensionScore(
                dimension=category_name,
                score=round(score, 2),
                weight=weight,
                details={
                    "matched_count": matched_count,
                    "total_count": total_count,
                    "weighted_score": round(weighted_score, 2),
                    "matched_skills": [s.name for s in category_skills if s.matched],
                    "missing_skills": list(jd_skills - set(s.name for s in category_skills if s.matched))
                }
            ))

        return dimension_scores

    def _calculate_overall_score_with_dynamic_weights(
        self,
        dimension_scores: List[DimensionScore],
        dynamic_weights: Dict[str, float]
    ) -> float:
        """计算总体加权得分（使用动态权重）"""
        if not dimension_scores:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for dim in dimension_scores:
            # 使用动态权重
            weight = dynamic_weights.get(dim.dimension, dim.weight)
            total_weighted_score += dim.score * weight
            total_weight += weight

        return (total_weighted_score / total_weight) if total_weight > 0 else 0.0

    def _calculate_skill_confidence(
        self,
        skill: str,
        category: str,
        found_in_jd: bool,
        found_in_resume: bool
    ) -> float:
        """计算单个技能的匹配置信度"""
        if not found_in_jd or not found_in_resume:
            return 0.0

        # 基础置信度
        confidence = 1.0

        # 根据类别调整置信度
        category_confidence_factors = {
            "core_tech": 0.95,    # 核心技术匹配置信度高
            "framework": 0.90,    # 框架匹配置信度较高
            "tool": 0.85,         # 工具匹配置信度中等
            "soft_skill": 0.80    # 软技能匹配置信度相对较低
        }

        confidence *= category_confidence_factors.get(category, 0.85)

        # 根据技能名称长度调整（越长越具体，置信度越高）
        if len(skill) >= 8:
            confidence *= 1.05
        elif len(skill) <= 3:
            confidence *= 0.95

        return min(confidence, 1.0)

    def _calculate_dimension_scores(
        self,
        weighted_skills: List[WeightedSkill],
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any]
    ) -> List[DimensionScore]:
        """计算各维度得分"""
        dimension_scores = []
        jd_by_category = jd_keywords_result.get("by_category", {})

        for category_name, category_data in KEYWORD_CATEGORIES.items():
            weight = category_data["weight"]
            jd_skills = set(jd_by_category.get(category_name, []))

            # 获取该类别的技能
            category_skills = [s for s in weighted_skills if s.category == category_name]

            if not jd_skills:
                # JD中没有该类别的技能要求
                dimension_scores.append(DimensionScore(
                    dimension=category_name,
                    score=100.0,  # 默认满分
                    weight=weight,
                    details={"reason": "JD中无此类别要求"}
                ))
                continue

            # 计算匹配数
            matched_count = sum(1 for s in category_skills if s.matched)
            total_count = len(jd_skills)

            # 计算得分
            score = (matched_count / total_count * 100) if total_count > 0 else 0

            # 加权得分
            weighted_score = score * weight

            dimension_scores.append(DimensionScore(
                dimension=category_name,
                score=round(score, 2),
                weight=weight,
                details={
                    "matched_count": matched_count,
                    "total_count": total_count,
                    "weighted_score": round(weighted_score, 2),
                    "matched_skills": [s.name for s in category_skills if s.matched],
                    "missing_skills": list(jd_skills - set(s.name for s in category_skills if s.matched))
                }
            ))

        return dimension_scores

    def _calculate_overall_score(self, dimension_scores: List[DimensionScore]) -> float:
        """计算总体加权得分"""
        if not dimension_scores:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for dim in dimension_scores:
            total_weighted_score += dim.score * dim.weight
            total_weight += dim.weight

        return (total_weighted_score / total_weight) if total_weight > 0 else 0.0

    def _calculate_confidence(
        self,
        weighted_skills: List[WeightedSkill],
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any]
    ) -> float:
        """
        计算匹配结果的总体置信度

        基于以下因素：
        1. JD和简历中提取的关键词数量
        2. 技能匹配的置信度
        3. 类别覆盖的完整性
        """
        jd_keywords = jd_keywords_result.get("keywords", [])
        resume_keywords = resume_keywords_result.get("keywords", [])

        if not jd_keywords:
            return 0.0

        # 1. 基于关键词数量的置信度
        keyword_count_confidence = min(len(jd_keywords) / 5, 1.0)  # 至少5个关键词达到满置信度

        # 2. 基于匹配技能平均置信度
        matched_skills = [s for s in weighted_skills if s.matched]
        if matched_skills:
            avg_skill_confidence = sum(s.confidence for s in matched_skills) / len(matched_skills)
        else:
            avg_skill_confidence = 0.0

        # 3. 基于类别覆盖的置信度
        categories_with_jd = set()
        categories_with_match = set()

        for skill in weighted_skills:
            if skill.found_in_jd:
                categories_with_jd.add(skill.category)
            if skill.matched:
                categories_with_match.add(skill.category)

        category_coverage = (len(categories_with_match) / len(categories_with_jd)
                           if categories_with_jd else 0.0)

        # 4. 基于简历丰富度的置信度
        resume_richness = min(len(resume_keywords) / 10, 1.0)  # 至少10个关键词达到满置信度

        # 加权组合
        confidence = (
            keyword_count_confidence * 0.25 +
            avg_skill_confidence * 0.35 +
            category_coverage * 0.25 +
            resume_richness * 0.15
        )

        return min(max(confidence, 0.0), 1.0)

    def _build_skill_match_result(self, weighted_skills: List[WeightedSkill]) -> Dict[str, List[str]]:
        """构建技能匹配结果"""
        matched = []
        missing = []
        extra = []

        for skill in weighted_skills:
            if skill.matched:
                matched.append(skill.name)
            elif skill.found_in_jd and not skill.found_in_resume:
                missing.append(skill.name)
            elif skill.found_in_resume and not skill.found_in_jd:
                extra.append(skill.name)

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra
        }

    def _build_match_details(
        self,
        weighted_skills: List[WeightedSkill],
        dimension_scores: List[DimensionScore],
        jd_keywords_result: Dict[str, Any],
        resume_keywords_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建详细匹配信息"""
        by_category = []

        for dim_score in dimension_scores:
            category_skills = [s for s in weighted_skills if s.category == dim_score.dimension]

            by_category.append({
                "category": dim_score.dimension,
                "score": dim_score.score,
                "weight": dim_score.weight,
                "matched": [s.name for s in category_skills if s.matched],
                "missing": [s.name for s in category_skills if s.found_in_jd and not s.found_in_resume],
                "extra": [s.name for s in category_skills if s.found_in_resume and not s.found_in_jd],
                "details": dim_score.details
            })

        return {
            "by_category": by_category,
            "total_jd_keywords": len(jd_keywords_result.get("keywords", [])),
            "total_resume_keywords": len(resume_keywords_result.get("keywords", [])),
            "total_matched": len([s for s in weighted_skills if s.matched]),
            "weighted_skills": [
                {
                    "name": s.name,
                    "category": s.category,
                    "weight": s.weight,
                    "matched": s.matched,
                    "confidence": s.confidence
                }
                for s in weighted_skills
            ]
        }

    def _calculate_match_score(self, jd_keywords: List[str], resume_keywords: List[str]) -> int:
        """计算匹配度分数"""
        if not jd_keywords:
            return 0

        matched = set(jd_keywords) & set(resume_keywords)
        score = int(len(matched) / len(jd_keywords) * 100)
        return min(score, 100)

    def analyze_match(self, vault_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        """
        分析 JD 与简历的匹配度
        双轨制：支持基础模式和 LLM 模式
        """
        logger.info("Starting match analysis")

        # 从 JD 提取关键词
        jd_keywords = self._extract_keywords(jd_text)
        logger.info(f"Extracted {len(jd_keywords)} keywords from JD")

        # 从简历提取关键词
        resume_text = json.dumps(vault_data, ensure_ascii=False)
        resume_keywords = self._extract_keywords(resume_text)
        logger.info(f"Extracted {len(resume_keywords)} keywords from resume")

        # 计算匹配
        matched_keywords = list(set(jd_keywords) & set(resume_keywords))
        missing_keywords = list(set(jd_keywords) - set(resume_keywords))

        # 计算分数
        score = self._calculate_match_score(jd_keywords, resume_keywords)

        analysis = {
            "overall_score": score,
            "skill_match": {
                "matched": matched_keywords[:20],  # 限制数量
                "missing": missing_keywords[:20]
            },
            "suggestions": self._generate_suggestions(matched_keywords, missing_keywords)
        }

        logger.info(f"Match analysis complete. Score: {score}")
        return analysis

    def _generate_suggestions(self, matched: List[str], missing: List[str]) -> List[str]:
        """生成优化建议"""
        suggestions = []

        if matched:
            suggestions.append(f"您的简历已涵盖以下关键技能：{', '.join(matched[:5])}")

        if missing:
            suggestions.append(f"建议补充以下技能关键词：{', '.join(missing[:5])}")
            suggestions.append("在简历中突出与目标岗位相关的项目经验")
        else:
            suggestions.append("您的技能匹配度很高！建议进一步量化项目成果")

        return suggestions

    def tailor_resume(
        self,
        vault_data: Dict[str, Any],
        jd_text: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成定制简历
        双轨制：
        - 无 API Key：基础模式（高亮匹配关键词）
        - 有 API Key：LLM 定制模式
        """
        logger.info("Starting resume tailoring")

        # 检查是否有 LLM 配置
        llm_client = self._get_llm_client(llm_config)

        if not llm_client:
            # 基础模式：返回带高亮的原始简历
            logger.info("Using fallback mode (no LLM)")
            return self._tailor_resume_fallback(vault_data, jd_text)

        # LLM 模式
        logger.info("Using LLM mode")
        return self._tailor_resume_llm(vault_data, jd_text, llm_client)

    def _tailor_resume_fallback(self, vault_data: Dict[str, Any], jd_text: str) -> str:
        """基础模式：高亮匹配关键词"""
        jd_keywords = self._extract_keywords(jd_text)
        resume_text = vault_data.get("raw_text_preview", "")

        # 提取匹配段落
        matched_sections = []
        lines = resume_text.split('\n')
        current_section = []

        for line in lines:
            line_keywords = self._extract_keywords(line)
            if set(line_keywords) & set(jd_keywords):
                current_section.append(line)
            elif current_section:
                if len(current_section) >= 2:  # 至少 2 行才算一个段落
                    matched_sections.append('\n'.join(current_section))
                current_section = []

        # 添加最后一段
        if current_section and len(current_section) >= 2:
            matched_sections.append('\n'.join(current_section))

        # 生成报告
        report = f"""# 简历定制报告（基础模式）

> ⚠️ **提示**：由于未配置大模型 API Key，系统仅为您提取了以下命中关键词的经历。建议配置 API Key 以获得 AI 智能定制功能。

## 目标岗位关键词分析

从 JD 中提取到的关键技能：
{chr(10).join(['- ' + kw for kw in jd_keywords[:15]])}

## 匹配段落高亮

以下段落包含与 JD 匹配的关键词：

{chr(10).join(['---\n**匹配段落 ' + str(i+1) + '：**\n```\n' + section + '\n```' for i, section in enumerate(matched_sections[:5])])}

## 优化建议

1. 在以上高亮段落中，确保突出显示与岗位相关的技能
2. 使用 JD 中的关键词来描述您的经历
3. 量化您的成果（如：提升性能 30%，处理 100万+ 数据等）
4. 补充缺失的关键技能：{', '.join([kw for kw in jd_keywords[:5] if kw not in self._extract_keywords(resume_text)])}

---
*原始简历文本预览：*

{resume_text[:1000]}...
"""

        return report

    def _tailor_resume_llm(
        self,
        vault_data: Dict[str, Any],
        jd_text: str,
        llm_client
    ) -> Dict[str, Any]:
        """
        LLM 模式：AI 智能定制（带防幻觉校验）
        
        Returns:
            Dict: 包含生成的简历和校验结果
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        from app.services.hallucination_service import get_hallucination_service

        # Step 1: 提取与对标（Extraction & Mapping）
        system_prompt_step1 = """你是高级简历顾问。请分析岗位JD，提取核心技能要求，并与候选人简历进行映射。

任务：
1. 从JD中提取前10个核心硬技能和软技能
2. 在候选人简历中寻找能够证明这些技能的经历
3. 输出技能映射表

输出JSON格式：
{
  "required_skills": ["技能1", "技能2", ...],
  "skill_mapping": {
    "技能1": {
      "found_in_resume": true/false,
      "evidence": "简历中的具体证据",
      "confidence": 0-1
    }
  },
  "missing_skills": ["缺失技能1", ...],
  "highlight_projects": ["需要突出的项目1", ...]
}

只返回JSON，不要其他文本。"""

        messages_step1 = [
            SystemMessage(content=system_prompt_step1),
            HumanMessage(content=f"岗位 JD：\n{jd_text}\n\n候选人简历数据：\n{json.dumps(vault_data, ensure_ascii=False, indent=2)}")
        ]

        try:
            response_step1 = llm_client.invoke(messages_step1)
            mapping_result = json.loads(response_step1.content)
            logger.info(f"Step 1 - Skill mapping completed. Missing skills: {mapping_result.get('missing_skills', [])}")
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            mapping_result = {"required_skills": [], "skill_mapping": {}, "missing_skills": [], "highlight_projects": []}

        # Step 2: 严格重写（Strict Rewriting）
        system_prompt_step2 = """你是高级简历顾问。你只能使用候选人简历中提供的事实。

任务：根据技能映射关系，重写工作经历描述，突出与JD匹配的技能。

严格规则：
1. 只能使用简历中提到的技术栈和项目经验
2. 可以调整语序、突出关键词、使用更专业的表达方式
3. 绝对禁止添加简历中未提及的技术栈或虚构项目数据
4. 工作经历描述使用 STAR 法则
5. 突出量化成果

输出 Markdown 格式的完整简历。"""

        messages_step2 = [
            SystemMessage(content=system_prompt_step2),
            HumanMessage(content=f"技能映射：\n{json.dumps(mapping_result, ensure_ascii=False, indent=2)}\n\n候选人简历数据：\n{json.dumps(vault_data, ensure_ascii=False, indent=2)}")
        ]

        try:
            response_step2 = llm_client.invoke(messages_step2)
            generated_resume = response_step2.content
            logger.info("Step 2 - Resume generation completed")
        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            return {
                "resume": self._tailor_resume_fallback(vault_data, jd_text),
                "verification": {"verified": False, "error": str(e)},
                "mapping": mapping_result
            }

        # Step 3: 校验与Diff（Verification）
        hallucination_service = get_hallucination_service()
        verification_result = hallucination_service.verify_resume_generation(
            vault_data,
            generated_resume,
            return_details=True
        )
        
        logger.info(f"Step 3 - Verification completed. Level: {verification_result['hallucination_level']}, Confidence: {verification_result['confidence_score']}")

        # 如果幻觉风险高，尝试重新生成（最多重试1次）
        if verification_result['hallucination_level'] == 'high' and verification_result['suspicious_count'] > 5:
            logger.warning("High hallucination detected, attempting regeneration with stricter prompt")
            
            # 使用更严格的Prompt重新生成
            strict_prompt = system_prompt_step2 + """

⚠️ 重要提醒：系统检测到您可能添加了简历中未提及的内容。请严格遵守：
- 只使用候选人明确提到的技术栈
- 不要虚构任何项目经验
- 所有描述必须基于真实经历
- 如果不确定，请省略该内容
"""
            messages_retry = [
                SystemMessage(content=strict_prompt),
                HumanMessage(content=f"请重新生成，确保所有内容来自简历：\n{json.dumps(vault_data, ensure_ascii=False, indent=2)}")
            ]
            
            try:
                response_retry = llm_client.invoke(messages_retry)
                generated_resume = response_retry.content
                
                # 重新校验
                verification_result = hallucination_service.verify_resume_generation(
                    vault_data,
                    generated_resume,
                    return_details=True
                )
                logger.info(f"Regeneration verification. Level: {verification_result['hallucination_level']}")
            except Exception as e:
                logger.error(f"Regeneration failed: {e}")

        return {
            "resume": generated_resume,
            "verification": verification_result,
            "mapping": mapping_result
        }

    def tailor_resume(
        self,
        vault_data: Dict[str, Any],
        jd_text: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成定制简历（统一返回格式）
        
        Returns:
            Dict: {
                "resume": str,  # Markdown格式简历
                "verification": Dict,  # 校验结果
                "mapping": Dict,  # 技能映射（LLM模式）
                "mode": str  # "llm" 或 "fallback"
            }
        """
        logger.info("Starting resume tailoring")

        # 检查是否有 LLM 配置
        llm_client = self._get_llm_client(llm_config)

        if not llm_client:
            # 基础模式
            logger.info("Using fallback mode (no LLM)")
            return {
                "resume": self._tailor_resume_fallback(vault_data, jd_text),
                "verification": {"verified": True, "mode": "fallback"},
                "mapping": {},
                "mode": "fallback"
            }

        # LLM 模式
        logger.info("Using LLM mode with hallucination check")
        result = self._tailor_resume_llm(vault_data, jd_text, llm_client)
        result["mode"] = "llm"
        return result

    def parse_resume_with_llm(self, resume_text: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用 LLM 解析简历"""
        llm_client = self._get_llm_client(llm_config)

        if not llm_client:
            logger.info("No LLM config, skipping LLM parsing")
            return {}

        from langchain_core.messages import HumanMessage, SystemMessage

        system_prompt = """你是一个专业的简历解析助手。请从简历文本中提取结构化信息，并以 JSON 格式返回。

输出格式：
{
  "personal_info": {
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话",
    "linkedin": "LinkedIn链接（可选）",
    "website": "个人网站（可选）"
  },
  "education": [
    {
      "school": "学校名称",
      "degree": "学位",
      "field": "专业",
      "start_date": "开始时间",
      "end_date": "结束时间"
    }
  ],
  "skills": [
    {
      "name": "技能名称",
      "level": "expert/proficient/familiar",
      "category": "技能类别"
    }
  ],
  "experiences": [
    {
      "company": "公司名称",
      "title": "职位",
      "start_date": "开始时间",
      "end_date": "结束时间",
      "projects": [
        {
          "name": "项目名称",
          "description": "项目描述",
          "technologies": ["技术栈"],
          "star_description": "STAR法则描述"
        }
      ]
    }
  ]
}

注意：只返回 JSON，不要添加任何其他文本。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"请解析以下简历文本：\n\n{resume_text}")
        ]

        try:
            response = llm_client.invoke(messages)
            result = json.loads(response.content)
            logger.info("LLM resume parsing successful")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return {}

    async def generate_interview_questions(
        self,
        jd_text: str,
        resume_md: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成面试题"""
        llm_client = self._get_llm_client(llm_config)

        if not llm_client:
            # 基础模式：返回通用问题
            return self._generate_fallback_questions(jd_text)

        from langchain_core.messages import HumanMessage, SystemMessage

        system_prompt = """你现在是技术/业务主管。请阅读候选人的简历和岗位 JD，设计 5 个深度面试问题。

要求：
1. 只有真正做过这些项目的候选人才能回答出来
2. 不仅要问 'What'，还要问 'Why' 和 'How'
3. 问题要针对简历中的具体经历和 JD 的要求

输出 JSON 格式：
[
  {
    "question_text": "问题内容",
    "question_type": "technical/behavioral/situational",
    "intent_analysis": "考察意图",
    "suggested_answer_star": "STAR 框架建议回答",
    "difficulty": 1-5
  }
]

注意：只返回 JSON 数组，不要添加任何其他文本。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"岗位 JD：\n{jd_text}\n\n候选人简历：\n{resume_md}")
        ]

        try:
            response = llm_client.invoke(messages)
            result = json.loads(response.content)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Interview question generation failed: {e}")
            return self._generate_fallback_questions(jd_text)

    def _generate_fallback_questions(self, jd_text: str) -> List[Dict[str, Any]]:
        """基础模式：生成通用面试问题"""
        keywords = self._extract_keywords(jd_text)

        questions = [
            {
                "question_text": f"请介绍一下您在 {keywords[0] if keywords else '相关技术'} 方面的项目经验？",
                "question_type": "technical",
                "intent_analysis": "考察候选人对核心技术的掌握程度和实际项目经验",
                "suggested_answer_star": "S: 项目背景\nT: 您的职责\nA: 采取的行动\nR: 取得的成果",
                "difficulty": 3
            },
            {
                "question_text": "您遇到过最具挑战性的技术问题是什么？如何解决的？",
                "question_type": "situational",
                "intent_analysis": "考察候选人的问题解决能力和抗压能力",
                "suggested_answer_star": "S: 问题背景\nT: 您的任务\nA: 分析过程和解决方案\nR: 最终结果和学习",
                "difficulty": 4
            },
            {
                "question_text": "您如何保持技术学习？最近学习了什么新技术？",
                "question_type": "behavioral",
                "intent_analysis": "考察候选人的学习能力和技术热情",
                "suggested_answer_star": "S: 学习动机\nT: 学习目标\nA: 学习方法\nR: 应用成果",
                "difficulty": 2
            },
            {
                "question_text": "描述一次团队合作中遇到的冲突，您是如何处理的？",
                "question_type": "behavioral",
                "intent_analysis": "考察候选人的沟通协作能力",
                "suggested_answer_star": "S: 冲突背景\nT: 您的角色\nA: 沟通和行动\nR: 和解结果",
                "difficulty": 3
            },
            {
                "question_text": "您对我们公司/产品有什么了解？为什么想加入？",
                "question_type": "behavioral",
                "intent_analysis": "考察候选人的求职动机和准备工作",
                "suggested_answer_star": "S: 了解渠道\nT: 求职目标\nA: 做的准备\nR: 期望贡献",
                "difficulty": 2
            }
        ]

        return questions
