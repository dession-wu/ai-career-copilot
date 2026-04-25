from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Any, Optional


class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    website: Optional[str] = None


class Education(BaseModel):
    school: str
    degree: str
    field: str
    start_date: str
    end_date: str


class Skill(BaseModel):
    name: str
    level: str  # expert, proficient, familiar
    category: str


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]
    star_description: Optional[str] = None


class Experience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str
    projects: List[Project]


class StructuredData(BaseModel):
    personal_info: PersonalInfo
    education: List[Education]
    skills: List[Skill]
    experiences: List[Experience]


class CareerVaultBase(BaseModel):
    structured_data: Dict[str, Any]


class CareerVaultCreate(CareerVaultBase):
    pass


class CareerVaultUpdate(BaseModel):
    structured_data: Optional[Dict[str, Any]] = None


class CareerVaultResponse(CareerVaultBase):
    id: str
    user_id: str
    raw_content: Optional[str] = None
    parsed_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True
