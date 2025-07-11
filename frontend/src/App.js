import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from './context/AuthContext';
import LoginPage from './pages/LoginPage';

// 使用React.lazy进行代码分割
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage'));
const DataSourceDetail = lazy(() => import('./pages/DataSourceDetail'));

// 一个私有路由组件，用于保护需要登录的页面
const PrivateRoute = ({ children }) => {
  const { user, isLoading } = useContext(AuthContext);

  if (isLoading) {
    // 在验证用户身份时显示加载状态
    return <div>全应用加载中...</div>;
  }

  return user ? children : <Navigate to="/login" />;
};

const App = () => {
  return (
    <Suspense fallback={<div>页面加载中...</div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route 
          path="/dashboard" 
          element={<PrivateRoute><DashboardPage /></PrivateRoute>} 
        />
        <Route 
          path="/project/:projectId" 
          element={<PrivateRoute><ProjectDetailPage /></PrivateRoute>} 
        />
        <Route 
          path="/project/:projectId/data-source/:id" 
          element={<PrivateRoute><DataSourceDetail /></PrivateRoute>} 
        />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </Suspense>
  );
};

export default App; 