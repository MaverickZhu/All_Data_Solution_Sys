import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import * as api from '../services/api';

// 1. 创建Context
export const AuthContext = createContext(null);

// 2. 创建AuthProvider组件
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchUser = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const response = await api.getCurrentUser();
                setUser(response.data);
            } catch (error) {
                console.error("Failed to fetch user, token might be invalid.", error);
                localStorage.removeItem('token');
                setUser(null);
            }
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchUser();
    }, [fetchUser]);

    const login = useCallback(async (email, password) => {
        const response = await api.login(email, password);
        localStorage.setItem('token', response.data.access_token);
        await fetchUser();
    }, [fetchUser]);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setUser(null);
    }, []);

    const authContextValue = {
        user,
        isLoading,
        login,
        logout,
    };

    return (
        <AuthContext.Provider value={authContextValue}>
            {children}
        </AuthContext.Provider>
    );
};

// 3. 创建一个自定义Hook，简化Context的使用
export const useAuth = () => {
    return useContext(AuthContext);
}; 