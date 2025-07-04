import React, { createContext, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../services/api';

// 1. 创建Context
const AuthContext = createContext(null);

// 2. 创建AuthProvider组件
export const AuthProvider = ({ children }) => {
    const navigate = useNavigate();
    const [token, setToken] = useState(() => localStorage.getItem('token'));
    const isAuthenticated = !!token;

    const login = async (username, password) => {
        try {
            const response = await api.login(username, password);
            if (response.data && response.data.access_token) {
                const newToken = response.data.access_token;
                localStorage.setItem('token', newToken);
                setToken(newToken);
                navigate('/dashboard');
                return { success: true };
            }
            // This case might happen if the API returns 200 OK but no token.
            return { success: false, message: '登录失败，未能获取到访问令牌。' };
        } catch (error) {
            console.error("Login failed:", error);
            let errorMessage = '发生未知网络错误，请稍后再试。';
            if (error.response) {
                // The request was made and the server responded with a status code
                // that falls out of the range of 2xx
                errorMessage = error.response.data.detail || `服务器错误，状态码: ${error.response.status}`;
            } else if (error.request) {
                // The request was made but no response was received
                errorMessage = '无法连接到服务器，请检查您的网络连接。';
            } else {
                // Something happened in setting up the request that triggered an Error
                errorMessage = error.message;
            }
            return { success: false, message: errorMessage };
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        navigate('/login');
    };

    const value = {
        token,
        isAuthenticated,
        login,
        logout,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 3. 创建自定义Hook以便在组件中使用
export const useAuth = () => {
    return useContext(AuthContext);
}; 