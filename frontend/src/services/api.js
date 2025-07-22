import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8088';

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
    // Handle token expiration and unauthorized access
    if (error.response && error.response.status === 401) {
      console.warn('Authentication failed, clearing token and redirecting to login');
      localStorage.removeItem('token');
      // Use window.location.href for better compatibility
      window.location.href = '/login';
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

    // Create a separate axios instance for the login request to avoid header conflicts.
    const loginAxios = axios.create({
        baseURL: `${API_URL}/api/v1`,
    });

    return loginAxios.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(response => {
        // After a successful login, manually save the token to localStorage.
        // This is necessary because we are not using the global apiClient with its interceptors.
        if (response.data && response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }
        // Return the original response to maintain the promise chain.
        return response;
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
export const getDataSources = (projectId) => apiClient.get(`/projects/${projectId}/data_sources`);
export const getDataSourceDetail = (projectId, dataSourceId) => {
    return apiClient.get(`/projects/${projectId}/data_sources/${dataSourceId}`);
};

export const uploadDataSource = (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post(`/projects/${projectId}/data_sources`, formData, {
        headers: {
            ...apiClient.defaults.headers.common, // 保留通用头
            'Content-Type': 'multipart/form-data', // 设置特定的Content-Type
            // 拦截器会自动添加 Authorization, 这里无需手动处理
        },
    });
};

export const deleteDataSource = (projectId, dataSourceId) => {
    return apiClient.delete(`/projects/${projectId}/data_sources/${dataSourceId}`);
};

// Search
export const searchInProject = (projectId, query) => {
    return apiClient.post(`/projects/${projectId}/search`, { query });
};

// Video Analysis
export const startVideoDeepAnalysis = (dataSourceId) => {
    return apiClient.post(`/video-analysis/${dataSourceId}/analyze?analysis_type=semantic`);
};

export const getVideoAnalysisStatus = (analysisId) => {
    return apiClient.get(`/video-analysis/${analysisId}/status`);
};

export const getVideoAnalysisStatusByDataSource = (dataSourceId) => {
    return apiClient.get(`/video-analysis/data-source/${dataSourceId}/status`);
};

// 添加视频深度分析任务轮询方法
export const pollVideoAnalysisStatus = async (analysisId, onProgress, maxAttempts = 120) => { // 增加到120次 = 10分钟
    let attempts = 0;
    
    const poll = async () => {
        try {
            attempts++;
            const response = await getVideoAnalysisStatus(analysisId);
            const { 
                status, 
                processing_time, 
                error_message, 
                current_phase, 
                progress_percentage, 
                progress_message 
            } = response.data;
            
            // 调用进度回调 - 使用后端返回的真实进度数据
            if (onProgress) {
                onProgress({
                    status,
                    attempts,
                    maxAttempts,
                    processing_time,
                    error_message,
                    current_phase,
                    progress_percentage: progress_percentage || 0, // 使用后端返回的真实进度
                    progress_message,
                    progress: progress_percentage || (attempts <= 3 ? 5 : 0) // 优先使用后端进度，回退到简单估算
                });
            }
            
            // 检查完成状态
            if (status === 'COMPLETED') {
                return { status: 'completed', data: response.data };
            } else if (status === 'FAILED') {
                return { status: 'failed', error: error_message || '分析失败' };
            } else if (attempts >= maxAttempts) {
                return { status: 'timeout', error: '分析超时' };
            } else {
                // 继续轮询
                await new Promise(resolve => setTimeout(resolve, 5000)); // 5秒间隔
                return poll();
            }
        } catch (error) {
            // 轮询错误处理 - 在开发环境下显示详细错误
            if (process.env.NODE_ENV === 'development') {
                console.error('轮询视频分析状态失败:', error);
            }
            if (attempts >= maxAttempts) {
                return { status: 'error', error: '网络错误' };
            }
            // 网络错误时继续重试
            await new Promise(resolve => setTimeout(resolve, 5000));
            return poll();
        }
    };
    
    return poll();
};

export const getVideoAnalysisReport = (analysisId) => {
    return apiClient.get(`/video-analysis/${analysisId}/report`);
}; 