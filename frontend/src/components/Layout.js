import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children, title }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/', label: '仪表盘' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      <header className="bg-white/95 backdrop-blur-lg sticky top-0 z-40 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex-shrink-0 text-gray-900 font-bold text-lg">
                多模态智能数据分析平台
              </Link>
            </div>
            <div className="flex items-center gap-6">
              <nav className="hidden md:flex gap-4">
                {navLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      location.pathname === link.to
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
              {user && (
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600 hidden sm:block">
                    欢迎, {user.username}
                  </span>
                  <button
                    onClick={logout}
                    className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                  >
                    退出登录
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout; 