import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('@/lib/api', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn() } }));
import { api } from '@/lib/api';
import { useApplicationStore } from '@/stores/applicationStore';
describe('Application persistence failures', () => {
    beforeEach(() => { vi.clearAllMocks(); useApplicationStore.setState({ applications: [], loading: false }); });
    it('rejects failed saves instead of creating imaginary successful applications', async () => {
        vi.mocked(api.post).mockRejectedValue(new Error('offline'));
        await expect(useApplicationStore.getState().addApplication({ company_name: '公司', job_title: '岗位', jd_text: '要求' })).rejects.toThrow('offline');
        expect(useApplicationStore.getState().applications).toEqual([]);
    });
    it('does not replace failed loads with other peoples sample applications', async () => {
        vi.mocked(api.get).mockRejectedValue(new Error('offline'));
        await expect(useApplicationStore.getState().fetchApplications()).rejects.toThrow();
        expect(useApplicationStore.getState().applications).toEqual([]);
        expect(useApplicationStore.getState().loading).toBe(false);
    });
});
