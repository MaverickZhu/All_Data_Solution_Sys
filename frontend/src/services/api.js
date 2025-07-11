import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8008';

const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token updates from login
apiClient.interceptors.response.use(
  (response) => {
    // If the response from a login request contains a token, update localStorage.
    if (response.data && response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response;
  },
  (error) => {
    // Also handle token expiration here if needed, e.g., redirect to login
    if (error.response && error.response.status === 401) {
      // localStorage.removeItem('token');
      // window.location = '/login';
    }
    return Promise.reject(error);
  }
);


/**
 * Starts the data profiling task for a given data source.
 * @param {string} dataSourceId - The ID of the data source.
 * @param {string} projectId - The ID of the project.
 * @returns {Promise<object>} A promise that resolves to the task object (e.g., { task_id: "some-uuid" }).
 */
export const startDataProfiling = (dataSourceId, projectId) => {
  return apiClient.post(`/processing/profile/${dataSourceId}`, null, {
    params: {
      project_id: projectId
    }
  });
};

/**
 * Gets the status of a data profiling task.
 * @param {string} taskId - The ID of the task.
 * @returns {Promise<object>} A promise that resolves to the task status object.
 */
export const getTaskStatus = (taskId) => {
  return apiClient.get(`/processing/profile/${taskId}`);
};

/**
 * Logs in a user.
 * @param {string} username - The user's username.
 * @param {string} password - The user's password.
 * @returns {Promise<object>} A promise that resolves to the login response data (e.g., { access_token, token_type }).
 */
export const login = (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    // Use the global apiClient so that interceptors are applied.
    return apiClient.post(`/auth/token`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
};

// 项目管理相关
export const getProjects = () => apiClient.get('/projects/');
export const createProject = (projectData) => apiClient.post('/projects/', projectData);
export const getProject = (projectId) => apiClient.get(`/projects/${projectId}`);
export const updateProject = (projectId, projectData) => apiClient.put(`/projects/${projectId}`, projectData);
export const deleteProject = (projectId) => apiClient.delete(`/projects/${projectId}`);

// User
export const getCurrentUser = () => apiClient.get('/users/me');

// Data Sources
export const getDataSources = (projectId) => apiClient.get(`/projects/${projectId}/datasources/`);
export const getDataSourceDetail = (projectId, dataSourceId) => {
    return apiClient.get(`/projects/${projectId}/datasources/${dataSourceId}`);
};

export const uploadDataSource = (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post(`/projects/${projectId}/datasources/`, formData, {
        headers: {
            ...apiClient.defaults.headers.common, // 保留通用头
            'Content-Type': 'multipart/form-data', // 设置特定的Content-Type
            // 拦截器会自动添加 Authorization, 这里无需手动处理
        },
    });
};

export const deleteDataSource = (projectId, dataSourceId) => {
    return apiClient.delete(`/projects/${projectId}/datasources/${dataSourceId}`);
};

// Search
export const searchInProject = (projectId, query) => {
    return apiClient.post(`/projects/${projectId}/search`, { query });
}; 