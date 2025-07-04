import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import Button from './Button';

const Layout = ({ children, title }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo 和标题 */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900">
                  多模态智能数据分析平台
                </h1>
              </div>
            </div>
            
            {/* 右侧菜单 */}
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                仪表盘
              </Button>
              <Button 
                variant="secondary" 
                size="sm"
                onClick={handleLogout}
              >
                退出登录
              </Button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {title && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
          </div>
        )}
        {children}
      </main>
    </div>
  );
};

export default Layout; 