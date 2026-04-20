import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  signup: (email: string, password: string) =>
    api.post('/signup', { email, password }),
  login: (email: string, password: string) =>
    api.post('/login', { email, password }),
};

export const fileAPI = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listFiles: () => api.get('/files'),
  download: (filename: string) =>
    api.get(`/download/${filename}`, { responseType: 'blob' }),
  delete: (filename: string) => api.delete(`/delete/${filename}`),
};

export default api;
