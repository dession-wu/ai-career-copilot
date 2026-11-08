import axios from 'axios';

const operationSignature = (config: {method?: string;url?: string;data?: unknown}) => {
  let data=config.data;
  if(typeof data==='string'){try{data=JSON.parse(data)}catch{}}
  return JSON.stringify([config.method,config.url,data]);
};
const pendingOperations = new Map<string,string>();
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const createApiClient = (baseURL?: string) => {
  const client = axios.create({
    baseURL: baseURL || API_BASE_URL,
    timeout: 30000,
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
      const signature = operationSignature(config);
      let operation = pendingOperations.get(signature);
      if (!operation) { operation = globalThis.crypto.randomUUID(); pendingOperations.set(signature,operation); }
      config.headers['Idempotency-Key'] = operation;
      return config;
    },
    (error) => Promise.reject(error)
  );

  client.interceptors.response.use(
    (response) => { pendingOperations.delete(operationSignature(response.config)); return response; },
    (error) => {
      if (error.response?.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          // 只在非登录/注册页面时自动跳转，避免打断组件层的错误处理
          const pathname = window.location.pathname;
          const isAuthPage = pathname.includes('/login') || pathname.includes('/register');
          if (!isAuthPage) {
            const locale = pathname.startsWith('/en/') ? 'en' : 'zh';
            const next = pathname.replace(/^\/(zh|en)(?=\/)/, '') + window.location.search;
            window.location.assign(`/${locale}/login?next=${encodeURIComponent(next)}`);
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
