import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// 导入页面组件
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import DataSourceDetail from './pages/DataSourceDetail';

// 导入真正的 useAuth 钩子和 AuthProvider
import { useAuth } from './context/AuthContext';

// 受保护的路由组件
const PrivateRoute = ({ children }) => {
    const { isAuthenticated } = useAuth();
    return isAuthenticated ? children : <Navigate to="/login" />;
};

// 公共路由组件（已登录用户访问登录页时重定向到仪表盘）
const PublicRoute = ({ children }) => {
    const { isAuthenticated } = useAuth();
    return !isAuthenticated ? children : <Navigate to="/dashboard" />;
};

function App() {
    return (
        <Routes>
            {/* 公共路由 */}
            <Route 
                path="/login" 
                element={
                    <PublicRoute>
                        <LoginPage />
                    </PublicRoute>
                } 
            />
            
            {/* 私有路由 */}
            <Route 
                path="/dashboard" 
                element={
                    <PrivateRoute>
                        <DashboardPage />
                    </PrivateRoute>
                } 
            />
            
            <Route 
                path="/projects/:projectId" 
                element={
                    <PrivateRoute>
                        <ProjectDetailPage />
                    </PrivateRoute>
                } 
            />
            
            <Route 
                path="/data-source/:dataSourceId" 
                element={
                    <PrivateRoute>
                        <DataSourceDetail />
                    </PrivateRoute>
                } 
            />
            
            {/* 默认重定向 */}
            <Route path="/" element={<Navigate to="/dashboard" />} />
            
            {/* 404 页面 */}
            <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
    );
}

export default App; 