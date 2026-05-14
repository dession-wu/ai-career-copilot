export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  linkedin?: string;
  website?: string;
}

export interface Education {
  school: string;
  degree: string;
  field: string;
  start_date: string;
  end_date: string;
}

export interface Skill {
  name: string;
  level: 'expert' | 'proficient' | 'familiar';
  category: string;
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  star_description?: string;
}

export interface Experience {
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  projects: Project[];
}

export interface CareerVault {
  id: string;
  raw_content: string;
  structured_data: {
    personal_info: PersonalInfo;
    education: Education[];
    skills: Skill[];
    experiences: Experience[];
  };
  parsed_at: string;
  updated_at: string;
}

export interface JobApplication {
  id: string;
  company_name: string;
  job_title: string;
  jd_text: string;
  status: 'preparing' | 'applied' | 'interviewing' | 'offered' | 'rejected';
  match_score?: number;
  match_analysis?: {
    overall_score: number;
    skill_match: {
      matched: string[];
      missing: string[];
    };
    suggestions: string[];
  };
  tailored_resume_md?: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewQuestion {
  id: string;
  question_text: string;
  question_type: 'technical' | 'behavioral' | 'situational';
  intent_analysis: string;
  suggested_answer_star: string;
  difficulty: number;
}

export interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
    status?: number;
  };
  message?: string;
}
