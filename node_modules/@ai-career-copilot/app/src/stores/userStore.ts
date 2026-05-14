import { create } from "zustand";
import { api } from "@/lib/api";

export interface User {
  id: number;
  username: string;
  email: string;
  name?: string;
  title?: string;
  phone?: string;
  bio?: string;
  avatar?: string;
}

interface UserState {
  user: User | null;
  loading: boolean;
  error: string | null;
  fetchUser: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  loading: false,
  error: null,

  fetchUser: async () => {
    set({ loading: true, error: null });
    try {
      const response = await api.get("/api/users/me");
      set({ user: response.data, loading: false });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      // 如果后端未实现，使用 mock 数据
      const mockUser: User = {
        id: 1,
        username: localStorage.getItem("username") || "user",
        email: "user@example.com",
        name: "求职者",
        title: "前端工程师",
        phone: "138****8888",
        bio: "热爱技术，追求极致用户体验",
      };
      set({ user: mockUser, loading: false });
      console.log("Using mock user data:", error.response?.data?.detail);
    }
  },

  updateUser: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await api.put("/api/users/me", data);
      set({ user: response.data, loading: false });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      // 更新本地状态（mock 模式）
      set((state) => ({
        user: state.user ? { ...state.user, ...data } : null,
        loading: false,
      }));
      console.log("Using local update:", error.response?.data?.detail);
    }
  },

  clearError: () => set({ error: null }),
}));
