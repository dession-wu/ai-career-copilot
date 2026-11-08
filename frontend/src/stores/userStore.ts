import { create } from 'zustand';
import { api } from '@/lib/api';
import { errorMessage } from '@/lib/career';
export interface User {
    id: string;
    username: string;
    email: string;
    created_at: string;
}
interface UserState {
    user: User | null;
    loading: boolean;
    error: string | null;
    fetchUser: () => Promise<void>;
    clearError: () => void;
}
export const useUserStore = create<UserState>((set) => ({ user: null, loading: false, error: null, fetchUser: async () => { set({ loading: true, error: null }); try {
        set({ user: (await api.get<User>('/api/auth/me')).data });
    }
    catch (e) {
        set({ error: errorMessage(e), user: null });
        throw e;
    }
    finally {
        set({ loading: false });
    } }, clearError: () => set({ error: null }) }));
