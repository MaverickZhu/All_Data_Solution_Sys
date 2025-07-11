import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import ProjectCard from '../components/ProjectCard';
import CreateProjectForm from '../components/CreateProjectForm';
import UserGuide from '../components/UserGuide'; // 引入UserGuide
import HelpTrigger from '../components/HelpTrigger'; // 引入HelpTrigger
import { getProjects, deleteProject } from '../services/api';

const DashboardPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [runTour, setRunTour] = useState(false); // 添加状态来控制引导

  useEffect(() => {
    const fetchProjectsAndCheckTour = async () => {
      try {
        setLoading(true);
        const response = await getProjects();
        setProjects(response.data);
        setError(null);
        // 如果没有项目，自动开始引导
        if (response.data.length === 0) {
          setRunTour(true);
        }
      } catch (err) {
        console.error('获取项目列表失败:', err);
        setError('获取项目列表失败，请稍后重试');
      } finally {
        setLoading(false);
      }
    };
    fetchProjectsAndCheckTour();
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

  const handleDeleteProject = useCallback(async (projectId) => {
    if (window.confirm('确定要删除这个项目吗？此操作不可撤销。')) {
      try {
        await deleteProject(projectId);
        setProjects(prev => prev.filter(project => project.id !== projectId));
      } catch (err) {
        console.error('删除项目失败:', err);
        alert('删除项目失败，请稍后重试');
      }
    }
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center pt-32">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-600 text-lg mt-4">正在加载项目...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
        {/* 页面头部 */}
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900">项目管理</h1>
          <p className="mt-2 text-lg text-gray-600">
            管理您的数据分析项目，创建新项目并上传数据源
          </p>
        </header>

        {/* 操作栏 */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-semibold text-gray-800">
                我的项目 <span className="text-blue-600">({projects.length})</span>
              </h2>
              <HelpTrigger
                title="关于项目管理"
                content={
                  <div>
                    <p className="mb-2">项目是您组织和管理所有数据分析工作的容器。</p>
                    <ul className="list-disc list-inside space-y-1 pl-4 mb-4">
                      <li><b>创建项目:</b> 点击右上角的“创建新项目”按钮开始一个新的分析任务。</li>
                      <li><b>查看项目:</b> 点击项目卡片上的“查看”按钮，进入项目详情页以上传和管理数据源。</li>
                      <li><b>刷新列表:</b> 如果您在其他地方创建了新项目，可以点击“刷新”按钮同步最新列表。</li>
                    </ul>
                    <h4 className="font-semibold text-gray-800 mt-4 mb-2">💡 使用技巧</h4>
                    <ul className="list-disc list-inside space-y-1 pl-4">
                        <li><b>清晰命名:</b> 为项目设置一个清晰、有描述性的名称和简介，将极大地帮助您在未来快速定位和管理分析任务。</li>
                        <li><b>任务隔离:</b> 建议为每一个独立的分析目标创建一个单独的项目，这有助于保持数据和结果的整洁与分离。</li>
                    </ul>
                  </div>
                }
              />
            </div>
            <button
              onClick={fetchProjects}
              className="px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-100 transition-colors duration-200 flex items-center gap-2"
            >
              🔄 刷新
            </button>
            <button
              onClick={() => setRunTour(true)}
              className="px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-100 transition-colors duration-200 flex items-center gap-2"
            >
              🚀 功能引导
            </button>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="create-project-button px-5 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-all duration-300 ease-in-out flex items-center gap-2"
          >
            ✨ 创建新项目
          </button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 border-l-4 border-red-500 bg-red-50 p-4">
            <div className="flex items-center gap-3">
              <div className="text-red-500 text-xl">⚠️</div>
              <div>
                <p className="text-red-800 font-medium">出错了</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
              <button
                onClick={fetchProjects}
                className="ml-auto px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-100"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* 项目列表 */}
        {projects.length === 0 && !loading ? (
          <div className="projects-list text-center py-24 bg-white rounded-xl border border-dashed border-gray-300">
            <div className="max-w-md mx-auto">
               <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
              </svg>
              <h3 className="mt-4 text-xl font-semibold text-gray-800">
                还没有项目
              </h3>
              <p className="mt-2 text-gray-500">
                创建您的第一个数据分析项目，开始探索数据的奥秘。
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="create-project-button mt-6 px-6 py-2.5 bg-blue-600 text-white font-bold rounded-lg shadow-sm hover:bg-blue-700"
              >
                创建第一个项目
              </button>
            </div>
          </div>
        ) : (
          <div className="projects-list grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={() => handleDeleteProject(project.id)}
              />
            ))}
          </div>
        )}

        {/* 创建项目模态框 */}
        <Modal
          title="创建新项目"
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
        >
          <CreateProjectForm
            onSuccess={handleCreateProject}
            onCancel={() => setShowCreateModal(false)}
          />
        </Modal>
        
        <UserGuide run={runTour} onTourEnd={() => setRunTour(false)} />
    </Layout>
  );
};

export default DashboardPage; 