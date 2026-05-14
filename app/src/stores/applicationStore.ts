import { create } from "zustand";
import { api } from "@/lib/api";

export interface Application {
  id: number;
  company: string;
  position: string;
  link?: string;
  salary?: string;
  channel: "官网" | "内推" | "猎头" | "其他";
  status: "投递中" | "面试中" | "已offer" | "已拒绝" | "已结束";
  note?: string;
  createdAt: string;
}

interface ApplicationState {
  applications: Application[];
  loading: boolean;
  fetchApplications: () => Promise<void>;
  addApplication: (data: Omit<Application, "id" | "createdAt" | "status">) => Promise<void>;
  updateStatus: (id: number, status: Application["status"]) => Promise<void>;
}

const mockApplications: Application[] = [
  {
    id: 1,
    company: "字节跳动",
    position: "前端工程师",
    link: "https://jobs.bytedance.com",
    salary: "25k-35k",
    channel: "官网",
    status: "面试中",
    note: "已通过一面，等待二面安排",
    createdAt: "2026-05-01T10:00:00Z",
  },
  {
    id: 2,
    company: "阿里巴巴",
    position: "高级前端开发",
    link: "https://talent.alibaba.com",
    salary: "30k-45k",
    channel: "内推",
    status: "投递中",
    note: "",
    createdAt: "2026-05-03T14:00:00Z",
  },
  {
    id: 3,
    company: "腾讯",
    position: "Web前端开发",
    salary: "28k-40k",
    channel: "官网",
    status: "已拒绝",
    note: "岗位已停止招聘",
    createdAt: "2026-04-28T09:00:00Z",
  },
];

// 用于在 mock 模式下持久化新增的数据
let mockApplicationsState = [...mockApplications];

export const useApplicationStore = create<ApplicationState>((set) => ({
  applications: [],
  loading: false,

  fetchApplications: async () => {
    set({ loading: true });
    try {
      const response = await api.get("/api/applications");
      set({ applications: response.data, loading: false });
    } catch {
      set({ applications: mockApplicationsState, loading: false });
    }
  },

  addApplication: async (data) => {
    try {
      const response = await api.post("/api/applications", data);
      set((state) => ({
        applications: [response.data, ...state.applications],
      }));
    } catch {
      // 本地添加
      const newApp: Application = {
        ...data,
        id: Date.now(),
        status: "投递中",
        createdAt: new Date().toISOString(),
      };
      mockApplicationsState = [newApp, ...mockApplicationsState];
      set((state) => ({
        applications: [newApp, ...state.applications],
      }));
    }
  },

  updateStatus: async (id, status) => {
    try {
      await api.put(`/api/applications/${id}`, { status });
    } catch {
      // 本地更新
    }
    set((state) => ({
      applications: state.applications.map((app) =>
        app.id === id ? { ...app, status } : app
      ),
    }));
  },
}));
