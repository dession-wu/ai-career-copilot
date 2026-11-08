import { create } from 'zustand';
import { api } from '@/lib/api';
import { Job, JobStatus, getJobs } from '@/lib/career';
export type Application = Job;
interface ApplicationState {
    applications: Job[];
    loading: boolean;
    fetchApplications: () => Promise<void>;
    addApplication: (data: {
        company_name: string;
        job_title: string;
        jd_text: string;
    }) => Promise<Job>;
    updateStatus: (id: string, status: JobStatus) => Promise<void>;
}
export const useApplicationStore = create<ApplicationState>((set) => ({ applications: [], loading: false, fetchApplications: async () => { set({ loading: true }); try {
        set({ applications: await getJobs() });
    }
    finally {
        set({ loading: false });
    } }, addApplication: async (data) => { const r = await api.post<Job>('/api/jobs', data); set(s => ({ applications: [r.data, ...s.applications] })); return r.data; }, updateStatus: async (id, status) => { const { data } = await api.put<Job>('/api/jobs/' + id + '/status', { status }); set(s => ({ applications: s.applications.map(j => j.id === id ? data : j) })); } }));
