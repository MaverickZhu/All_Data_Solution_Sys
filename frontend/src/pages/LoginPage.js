import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/Button';
import Input from '../components/Input';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData.username, formData.password);
      navigate('/dashboard');
    } catch (err) {
      console.error('登录失败:', err);
      setError('用户名或密码错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* 背景装饰元素 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-warning-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
      </div>

      {/* 登录卡片 */}
      <div className="card max-w-md w-full relative z-10">
        {/* 头部 */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🚀</div>
          <h1 className="text-3xl font-bold gradient-text mb-2">
            多模态智能数据分析平台
          </h1>
          <p className="text-gray-600">
            登录您的账户，开始数据探索之旅
          </p>
        </div>

        {/* 登录表单 */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 错误提示 */}
          {error && (
            <div className="card bg-error-50 border-error-200 border-l-4 border-l-error-500">
              <div className="flex items-center gap-3">
                <div className="text-error-500 text-lg">⚠️</div>
                <div>
                  <p className="text-error-700 font-medium">登录失败</p>
                  <p className="text-error-600 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* 用户名输入 */}
          <div className="input-group">
            <Input
              label="用户名"
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="请输入您的用户名"
              required
              className="input-field"
            />
          </div>

          {/* 密码输入 */}
          <div className="input-group">
            <Input
              label="密码"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="请输入您的密码"
              required
              className="input-field"
            />
          </div>

          {/* 登录按钮 */}
          <Button
            type="submit"
            variant="primary"
            className="w-full btn-lg"
            disabled={loading}
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="loading w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                登录中...
              </div>
            ) : (
              '🔐 登录'
            )}
          </Button>
        </form>

        {/* 底部信息 */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="text-center text-sm text-gray-600">
            <p className="mb-2">测试账户信息</p>
            <div className="glass rounded-lg p-3 text-left">
              <p><span className="font-medium">用户名:</span> demo</p>
              <p><span className="font-medium">密码:</span> password</p>
            </div>
          </div>
        </div>

        {/* 功能特性 */}
        <div className="mt-6">
          <div className="grid grid-cols-3 gap-4 text-center text-sm">
            <div className="glass rounded-lg p-3">
              <div className="text-xl mb-1">📊</div>
              <p className="text-gray-600">数据分析</p>
            </div>
            <div className="glass rounded-lg p-3">
              <div className="text-xl mb-1">🤖</div>
              <p className="text-gray-600">AI驱动</p>
            </div>
            <div className="glass rounded-lg p-3">
              <div className="text-xl mb-1">🔒</div>
              <p className="text-gray-600">安全可靠</p>
            </div>
          </div>
        </div>
      </div>

      {/* 页面底部 */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-center text-gray-500 text-sm">
        <p>© 2024 多模态智能数据分析平台. All rights reserved.</p>
      </div>
    </div>
  );
};

export default LoginPage; 