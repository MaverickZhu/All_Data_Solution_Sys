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

/**
 * Starts the data profiling task for a given data source.
 * @param {string} dataSourceId - The ID of the data source.
 * @param {string} projectId - The ID of the project the data source belongs to.
 * @returns {Promise<object>} A promise that resolves to the task object (e.g., { task_id: "some-uuid" }).
 */
export const startDataProfiling = (dataSourceId, projectId) => {
  if (!projectId) {
    return Promise.reject(new Error("Project ID is required to start profiling."));
  }
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

    // Use a separate, clean axios instance for the login request to avoid header conflicts.
    return axios.post(`${API_URL}/api/v1/auth/token`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
};

// 项目管理相关
export const getProjects = () => {
    return apiClient.get('/projects/');
};

export const createProject = (projectData) => {
    return apiClient.post('/projects/', projectData);
};

export const getProject = (projectId) => {
    return apiClient.get(`/projects/${projectId}`);
};

export const updateProject = (projectId, projectData) => {
    return apiClient.put(`/projects/${projectId}`, projectData);
};

export const deleteProject = (projectId) => {
    return apiClient.delete(`/projects/${projectId}`);
};

// 数据源管理相关
export const uploadDataSource = (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post(`/projects/${projectId}/datasources/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};

export const getDataSources = (projectId) => {
    return apiClient.get(`/projects/${projectId}/datasources/`);
};

export const deleteDataSource = (projectId, dataSourceId) => {
    return apiClient.delete(`/projects/${projectId}/datasources/${dataSourceId}`);
};

// 添加获取单个数据源详情的函数
export const getDataSourceDetail = (dataSourceId) => {
    return apiClient.get(`/data-sources/${dataSourceId}`);
}; 