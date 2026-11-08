// Notifications are not available in the current backend. Do not invent reminders.
import { create } from 'zustand';
export const useNotificationStore = create(() => ({ notifications: [], unreadCount: 0, loading: false }));
