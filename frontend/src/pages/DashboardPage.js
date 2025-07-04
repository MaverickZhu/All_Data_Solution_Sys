import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import Button from '../components/Button';
import Modal from '../components/Modal';
import ProjectCard from '../components/ProjectCard';
import CreateProjectForm from '../components/CreateProjectForm';
import { getProjects, deleteProject } from '../services/api';

const DashboardPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await getProjects();
      setProjects(response.data);
      setError(null);
    } catch (err) {
      console.error('获取项目列表失败:', err);
      setError('获取项目列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = (newProject) => {
    setProjects(prev => [...prev, newProject]);
    setShowCreateModal(false);
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('确定要删除这个项目吗？此操作不可撤销。')) {
      return;
    }

    try {
      await deleteProject(projectId);
      setProjects(prev => prev.filter(project => project.id !== projectId));
    } catch (err) {
      console.error('删除项目失败:', err);
      alert('删除项目失败，请稍后重试');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="main-container">
          <div className="flex items-center justify-center min-h-screen">
            <div className="card text-center">
              <div className="loading w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full mx-auto mb-4"></div>
              <p className="text-gray-600">加载中...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="main-container">
        {/* 页面头部 */}
        <div className="page-header">
          <h1 className="page-title">项目管理</h1>
          <p className="page-subtitle">
            管理您的数据分析项目，创建新项目并上传数据源
          </p>
        </div>

        {/* 操作栏 */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-semibold text-gray-800">
              我的项目 <span className="text-primary-600">({projects.length})</span>
            </h2>
            {projects.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchProjects}
                className="hover-lift"
              >
                🔄 刷新
              </Button>
            )}
          </div>
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
            className="btn-lg hover-lift"
          >
            ✨ 创建新项目
          </Button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="card mb-6 border-l-4 border-error-500 bg-error-50">
            <div className="flex items-center gap-3">
              <div className="text-error-500 text-xl">⚠️</div>
              <div>
                <p className="text-error-700 font-medium">出错了</p>
                <p className="text-error-600 text-sm">{error}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchProjects}
                className="ml-auto"
              >
                重试
              </Button>
            </div>
          </div>
        )}

        {/* 项目列表 */}
        {projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="card max-w-md mx-auto">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                还没有项目
              </h3>
              <p className="text-gray-600 mb-6">
                创建您的第一个数据分析项目，开始探索数据的奥秘
              </p>
              <Button
                variant="primary"
                onClick={() => setShowCreateModal(true)}
                className="btn-lg"
              >
                🚀 创建第一个项目
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div key={project.id} className="hover-lift">
                <ProjectCard
                  project={project}
                  onDelete={handleDeleteProject}
                />
              </div>
            ))}
          </div>
        )}

        {/* 创建项目模态框 */}
        {showCreateModal && (
          <Modal
            title="创建新项目"
            onClose={() => setShowCreateModal(false)}
          >
            <CreateProjectForm
              onSuccess={handleCreateProject}
              onCancel={() => setShowCreateModal(false)}
            />
          </Modal>
        )}
      </div>

      {/* 页面底部装饰 */}
      <div className="mt-20 text-center text-gray-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
          <span>多模态智能数据分析平台</span>
          <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
        </div>
        <p>让数据驱动决策，让智能赋能未来</p>
      </div>
    </Layout>
  );
};

export default DashboardPage; 