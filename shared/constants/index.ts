export const API_PATHS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    ME: '/api/auth/me',
  },
  VAULT: {
    BASE: '/api/vault',
    UPLOAD: '/api/vault/upload',
    REPARSE: '/api/vault/reparse',
    STATUS: '/api/vault/upload-status',
  },
  JOBS: {
    BASE: '/api/jobs',
    EXTRACT: '/api/jobs/extract',
    MATCH: '/api/jobs/match',
    TAILOR: '/api/jobs/tailor',
  },
  INTERVIEW: {
    BASE: '/api/interview',
    QUESTIONS: '/api/interview/questions',
  },
} as const;

export const JOB_STATUS = {
  PREPARING: 'preparing',
  APPLIED: 'applied',
  INTERVIEWING: 'interviewing',
  OFFERED: 'offered',
  REJECTED: 'rejected',
} as const;

export type JobStatusType = (typeof JOB_STATUS)[keyof typeof JOB_STATUS];

export const SKILL_LEVELS = {
  EXPERT: 'expert',
  PROFICIENT: 'proficient',
  FAMILIAR: 'familiar',
} as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const SUPPORTED_FILE_TYPES = ['.pdf', '.doc', '.docx'];
