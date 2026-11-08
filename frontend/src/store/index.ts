import { create } from 'zustand';
import { api } from '@/lib/api';
import type { User, JobApplication, CareerVault } from '@shared/types';

interface AppState {
  user: User | null;
  jobs: JobApplication[];
  vault: CareerVault | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  setUser: (user: User | null) => void;
  fetchJobs: () => Promise<void>;
  fetchVault: () => Promise<void>;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  jobs: [],
  vault: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  fetchJobs: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get("/api/jobs");
      set({ jobs: response.data, isLoading: false });
    } catch (err) {
      set({ error: "获取投递列表失败", isLoading: false });
    }
  },

  fetchVault: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get("/api/vault");
      set({ vault: response.data, isLoading: false });
    } catch (err) {
      set({ vault: null, isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, jobs: [], vault: null, isAuthenticated: false });
  },
}));

export const useIsAuthenticated = () => useAppStore((s) => s.isAuthenticated);
