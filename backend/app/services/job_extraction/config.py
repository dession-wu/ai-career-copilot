"""
职位信息提取配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class JobExtractionConfig:
    """职位信息提取配置"""
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = field(default_factory=lambda: [
        "image/png", "image/jpeg", "image/jpg", "image/webp"
    ])
    ALLOWED_DOCUMENT_TYPES: List[str] = field(default_factory=lambda: [
        "application/pdf"
    ])
    TEMP_FILE_DIR: str = "/tmp/job_extraction"
    
    # OCR配置
    OCR_LANGUAGE: str = "ch_sim+en"  # 简体中文+英文
    OCR_DPI: int = 300
    
    # 职位名称关键词库
    JOB_TITLE_KEYWORDS: List[str] = field(default_factory=lambda: [
        # 技术类
        "工程师", "开发", "架构师", "程序员", "技术员", "技术专家",
        "前端", "后端", "全栈", "客户端", "移动端", "iOS", "Android",
        "Java", "Python", "C++", "Go", "Rust", "PHP", "Node.js",
        "算法", "数据", "AI", "人工智能", "机器学习", "深度学习",
        "测试", "QA", "运维", "DevOps", "SRE", "安全",
        "产品", "项目经理", "产品经理", "项目助理",
        "设计", "UI", "UX", "视觉", "交互", "平面",
        "运营", "推广", "市场", "销售", "商务", "BD",
        "人事", "HR", "招聘", "行政", "财务", "会计", "出纳",
        "法务", "律师", "合规", "审计",
        "客服", "助理", "文员", "秘书",
        "管理", "总监", "经理", "主管", "组长", "负责人",
    ])
    
    # 职位级别
    JOB_LEVELS: List[str] = field(default_factory=lambda: [
        "初级", "中级", "高级", "资深", "专家", "首席", "助理", "实习"
    ])
    
    # 公司后缀
    COMPANY_SUFFIXES: List[str] = field(default_factory=lambda: [
        "公司", "集团", "科技", "网络", "软件", "信息", "技术",
        "咨询", "服务", "传媒", "文化", "教育", "医疗", "金融",
        "投资", "证券", "银行", "保险", "基金", "信托",
        "贸易", "实业", "制造", "工程", "建筑", "房地产",
        "电子商务", "电商", "互联网", "智能", "创新",
        "Corp", "Inc", "Ltd", "Limited", "Company", "Group"
    ])
    
    # 知名公司名库
    WELL_KNOWN_COMPANIES: List[str] = field(default_factory=lambda: [
        # 国内互联网
        "阿里巴巴", "腾讯", "字节跳动", "百度", "美团", "京东", "滴滴", 
        "快手", "拼多多", "网易", "小米", "华为", "OPPO", "vivo",
        "哔哩哔哩", "B站", "知乎", "微博", "小红书", "得物",
        # 国内金融
        "中国平安", "招商银行", "工商银行", "建设银行", "农业银行",
        "中国银行", "中信证券", "华泰证券", "国泰君安", "海通证券",
        # 外企
        "Google", "Microsoft", "Amazon", "Facebook", "Meta", "Apple",
        "Netflix", "Tesla", "Uber", "Airbnb", "LinkedIn", "Twitter",
        "IBM", "Oracle", "SAP", "Intel", "NVIDIA", "AMD", "Qualcomm",
        # 外企中文名
        "谷歌", "微软", "亚马逊", "脸书", "苹果", "特斯拉", "优步",
        "英特尔", "英伟达", "超微", "高通",
    ])
    
    # 地点关键词
    LOCATION_KEYWORDS: Dict[str, List[str]] = field(default_factory=lambda: {
        "provinces": [
            "北京", "上海", "天津", "重庆",
            "广东", "浙江", "江苏", "山东", "河南", "四川",
            "湖北", "湖南", "河北", "福建", "安徽", "陕西",
            "辽宁", "江西", "云南", "贵州", "山西", "广西",
            "内蒙古", "新疆", "西藏", "宁夏", "青海", "甘肃",
            "海南", "黑龙江", "吉林"
        ],
        "cities": [
            "广州", "深圳", "杭州", "南京", "苏州", "成都", "武汉",
            "西安", "郑州", "长沙", "青岛", "大连", "厦门", "宁波",
            "无锡", "佛山", "东莞", "沈阳", "济南", "合肥", "昆明",
            "南昌", "贵阳", "石家庄", "哈尔滨", "长春", "太原",
            "兰州", "海口", "南宁", "乌鲁木齐", "呼和浩特"
        ],
        "districts": [
            "海淀区", "朝阳区", "浦东新区", "南山区", "福田区",
            "天河区", "西湖区", "滨江区", "园区", "高新区"
        ]
    })
    
    # 远程工作关键词
    REMOTE_KEYWORDS: List[str] = field(default_factory=lambda: [
        "远程", "居家", "在家", "线上", "Remote", "Work From Home", "WFH",
        "分布式", "异地", "全国", "不限地点"
    ])
    
    # 薪资模式
    SALARY_PATTERNS: List[str] = field(default_factory=lambda: [
        r"(\d+)\s*[kK]\s*[-~]\s*(\d+)\s*[kK]",  # 10k-20k
        r"(\d+)\s*[-~]\s*(\d+)\s*[kK]",  # 10-20k
        r"(\d+)\s*万\s*[-~]\s*(\d+)\s*万",  # 10万-20万
        r"月薪\s*(\d+)[-~]?(\d*)",  # 月薪10000-20000
        r"年薪\s*(\d+)[-~]?(\d*)",  # 年薪20万-40万
        r"(\d+)\s*[-~]\s*(\d+)\s*元",  # 10000-20000元
    ])
    
    SALARY_UNITS: Dict[str, str] = field(default_factory=lambda: {
        "k": "月",
        "K": "月",
        "万": "年",
        "月薪": "月",
        "年薪": "年",
    })
    
    # 经验要求模式
    EXPERIENCE_PATTERNS: List[str] = field(default_factory=lambda: [
        r"(\d+)\s*年(?:及)?以上经验",
        r"(\d+)\s*[-~]\s*(\d+)\s*年经验",
        r"经验\s*(\d+)\s*年(?:及)?以上",
        r"(?:工作|相关)经验\s*(\d+)\s*年",
    ])
    
    EXPERIENCE_KEYWORDS: Dict[str, str] = field(default_factory=lambda: {
        "应届生": "应届生",
        "应届毕业生": "应届生",
        "无经验": "经验不限",
        "经验不限": "经验不限",
        "不限经验": "经验不限",
        "1年以内": "1年以内",
        "1年以上": "1-3年",
        "3年以上": "3-5年",
        "5年以上": "5-10年",
    })
    
    # 学历要求
    EDUCATION_KEYWORDS: Dict[str, str] = field(default_factory=lambda: {
        "博士": "博士",
        "硕士研究生": "硕士",
        "硕士": "硕士",
        "研究生": "硕士",
        "本科": "本科",
        "大学本科": "本科",
        "大专": "大专",
        "专科": "大专",
        "高中": "高中",
        "中专": "高中",
        "学历不限": "学历不限",
        "不限学历": "学历不限",
    })
    
    # 工作类型
    JOB_TYPE_KEYWORDS: Dict[str, str] = field(default_factory=lambda: {
        "全职": "全职",
        "全职工作": "全职",
        "兼职": "兼职",
        "兼职工作": "兼职",
        "实习": "实习",
        "实习生": "实习",
        "合同": "合同",
        "外包": "合同",
    })
    
    # 章节识别关键词
    SECTION_KEYWORDS: Dict[str, List[str]] = field(default_factory=lambda: {
        "job_description": [
            "岗位职责", "职位描述", "工作内容", "工作职责",
            "Job Description", "Responsibilities", "What You'll Do"
        ],
        "job_requirements": [
            "任职要求", "岗位要求", "任职资格", "职位要求",
            "Requirements", "Qualifications", "What We're Looking For"
        ],
        "benefits": [
            "福利待遇", "薪资福利", "员工福利", "公司福利",
            "Benefits", "Perks", "What We Offer"
        ],
        "company_intro": [
            "公司介绍", "关于我们", "企业简介", "公司概况",
            "About Us", "Company Overview", "Who We Are"
        ]
    })
    
    # 置信度阈值
    CONFIDENCE_THRESHOLD_HIGH: float = 0.8
    CONFIDENCE_THRESHOLD_MEDIUM: float = 0.6
    CONFIDENCE_THRESHOLD_LOW: float = 0.4
    
    # 准确率目标
    ACCURACY_TARGETS: Dict[str, float] = field(default_factory=lambda: {
        "job_title": 0.90,
        "company_name": 0.85,
        "location": 0.80,
        "salary": 0.75,
        "experience": 0.80,
        "education": 0.85,
        "job_description": 0.70,
        "job_requirements": 0.70,
    })


# 全局配置实例
config = JobExtractionConfig()
