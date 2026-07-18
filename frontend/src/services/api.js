import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
});

export const analyzeStock = (payload) => api.post('/analyze', payload).then((r) => r.data);
export const backtestStock = (payload) => api.post('/backtest', payload).then((r) => r.data);
export const searchSymbol = (q) => api.get(`/symbols/search?q=${q}`).then((r) => r.data);
export const healthCheck = () => api.get('/health').then((r) => r.data);

export default api;
