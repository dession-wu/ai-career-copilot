import { create } from "zustand";
import { api } from "@/lib/api";

export interface Notification {
  id: number;
  title: string;
  content: string;
  type: "system" | "business";
  read: boolean;
  createdAt: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  filter: "all" | "system" | "business";
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: number) => Promise<void>;
  setFilter: (filter: "all" | "system" | "business") => void;
}

const mockNotifications: Notification[] = [
  {
    id: 1,
    title: "面试提醒",
    content: "您有一个面试安排在明天 14:00，请提前准备",
    type: "business",
    read: false,
    createdAt: "2026-05-05T10:00:00Z",
  },
  {
    id: 2,
    title: "系统维护通知",
    content: "系统将于今晚 02:00-04:00 进行例行维护",
    type: "system",
    read: false,
    createdAt: "2026-05-05T08:00:00Z",
  },
  {
    id: 3,
    title: "投递状态更新",
    content: "您的阿里巴巴前端工程师投递已通过初筛",
    type: "business",
    read: true,
    createdAt: "2026-05-04T15:30:00Z",
  },
  {
    id: 4,
    title: "新功能上线",
    content: "数据分析功能已上线，快来查看您的求职数据吧",
    type: "system",
    read: true,
    createdAt: "2026-05-03T09:00:00Z",
  },
];

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  filter: "all",

  fetchNotifications: async () => {
    set({ loading: true });
    try {
      const response = await api.get("/api/notifications");
      const notifications = response.data;
      const unreadCount = notifications.filter((n: Notification) => !n.read).length;
      set({ notifications, unreadCount, loading: false });
    } catch {
      // 使用 mock 数据
      const unreadCount = mockNotifications.filter((n) => !n.read).length;
      set({ notifications: mockNotifications, unreadCount, loading: false });
    }
  },

  markAsRead: async (id) => {
    try {
      await api.put(`/api/notifications/${id}/read`);
    } catch {
      // 本地更新
    }
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      const unreadCount = notifications.filter((n) => !n.read).length;
      return { notifications, unreadCount };
    });
  },

  markAllAsRead: async () => {
    try {
      await api.put("/api/notifications/read-all");
    } catch {
      // 本地更新
    }
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }));
  },

  deleteNotification: async (id) => {
    try {
      await api.delete(`/api/notifications/${id}`);
    } catch {
      // 本地更新
    }
    set((state) => {
      const notifications = state.notifications.filter((n) => n.id !== id);
      const unreadCount = notifications.filter((n) => !n.read).length;
      return { notifications, unreadCount };
    });
  },

  setFilter: (filter) => set({ filter }),
}));
