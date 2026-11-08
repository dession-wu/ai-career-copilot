import axios from 'axios';
import { api } from '@/lib/api';
export const statuses = { preparing: '准备中', applied: '已投递', interviewing: '面试中', offered: '已获 Offer', rejected: '未通过' };
export type JobStatus = keyof typeof statuses;
export interface Analysis {
    overall_score: number;
    skill_match: {
        matched: string[];
        missing: string[];
        extra?: string[];
    };
    suggestions: string[];
    source_vault_version?: number;
    source_jd_text?: string;
    dimension_scores?: {
        dimension: string;
        score: number;
    }[];
}
export interface ResumeVersion {
    version: number;
    content: string;
    note?: string;
    created_at: string;
}
export interface Job {
    id: string;
    company_name: string;
    job_title: string;
    jd_text: string;
    status: JobStatus;
    created_at: string;
    updated_at: string;
    match_score: number | null;
    match_analysis: Analysis | null;
    tailored_resume_md: string | null;
    tailored_resume_versions?: ResumeVersion[];
}
export interface Vault {
    id: string;
    raw_content?: string;
    version: number;
    updated_at: string;
    structured_data: Record<string, unknown>;
}
export interface Question {
    id: string;
    question_text: string;
    question_type?: string;
    intent_analysis?: string;
    suggested_answer_star?: string;
}
export function errorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === 'string')
            return detail;
        if (Array.isArray(detail))
            return '提交内容不符合要求，请检查必填字段。';
        if (error.code === 'ECONNABORTED')
            return '处理时间较长，请稍后刷新查看结果，避免重复提交。';
        if (!error.response)
            return '暂时无法连接服务，请检查网络后重试。';
        return `操作未完成（${error.response.status}），请稍后重试。`;
    }
    return error instanceof Error ? error.message : '操作未完成，请重试。';
}
export const getJobs = async () => (await api.get<Job[]>('/api/jobs')).data;
export async function getVault(): Promise<Vault | null> {
    try {
        return (await api.get<Vault>('/api/vault')).data;
    }
    catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404)
            return null;
        throw error;
    }
}
export const jobPath = (id: string, tab?: string) => `/jobs/detail?id=${encodeURIComponent(id)}${tab ? `&tab=${tab}` : ''}`;
export const confirmed = (vault: Vault | null) => Boolean(vault?.structured_data._confirmed);
export function staleAnalysis(job: Job, vault: Vault | null) { const a = job.match_analysis; return Boolean(a && (!a.source_vault_version || a.source_vault_version !== vault?.version || a.source_jd_text !== job.jd_text)); }
export function dateLabel(value?: string) { return value ? new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`).toLocaleDateString('zh-CN') : '—'; }
export function downloadBlob(blob: Blob, filename: string) { const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = filename; a.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); }
