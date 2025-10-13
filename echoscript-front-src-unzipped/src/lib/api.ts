import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true, // Send cookies with requests
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // You can add global error handling here
    return Promise.reject(error);
  }
);

export default apiClient;