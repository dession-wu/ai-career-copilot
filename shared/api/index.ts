import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const createApiClient = (baseURL?: string) => {
  const client = axios.create({
    baseURL: baseURL || API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  client.interceptors.request.use(
    (config) => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          // 只在非登录/注册页面时自动跳转，避免打断组件层的错误处理
          const pathname = window.location.pathname;
          const isAuthPage = pathname.includes('/login') || pathname.includes('/register');
          if (!isAuthPage) {
            window.location.assign('/login');
          }
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const api = createApiClient();
export default api;
