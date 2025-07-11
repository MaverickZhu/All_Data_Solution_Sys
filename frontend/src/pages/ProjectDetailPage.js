import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import { getProject, getDataSources, deleteDataSource } from '../services/api';
import DataSourceUpload from '../components/DataSourceUpload';
import ProjectSearch from '../components/ProjectSearch';
import HelpTrigger from '../components/HelpTrigger'; // 引入HelpTrigger
import { PlusIcon, ChartBarIcon, ClockIcon, TagIcon, FolderIcon as DatabaseIcon, TrashIcon } from '@heroicons/react/24/solid';

const ProjectDetailPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [dataSources, setDataSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);

  const fetchProjectData = useCallback(async () => {
    try {
      setLoading(true);
      const projectResponse = await getProject(projectId);
      const dataSourcesResponse = await getDataSources(projectId);
      
      setProject(projectResponse.data);
      setDataSources(dataSourcesResponse.data);
      setError(null);
    } catch (err) {
      console.error('获取项目数据失败:', err);
      setError('获取项目数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  const handleUploadSuccess = () => {
    setUploadModalOpen(false);
    fetchProjectData();
  };

  const handleDeleteDataSource = async (dataSourceId) => {
    if (!window.confirm('确定要删除这个数据源吗？此操作不可恢复。')) {
      return;
    }

    try {
      await deleteDataSource(projectId, dataSourceId);
      setDataSources(prev => prev.filter(ds => ds.id !== dataSourceId));
    } catch (err) {
      console.error('删除数据源失败:', err);
      alert('删除数据源失败，请稍后重试');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0 || !bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN', { hour12: false });
  };
  
  const getStatusChip = (status) => {
    const baseClasses = "px-3 py-1 text-xs font-semibold rounded-full inline-flex items-center gap-1.5";
    switch (status) {
      case 'completed':
        return <span className={`${baseClasses} bg-green-500/10 text-green-300`}><span className="h-1.5 w-1.5 rounded-full bg-green-400"></span>已完成</span>;
      case 'in_progress':
        return <span className={`${baseClasses} bg-yellow-500/10 text-yellow-300 animate-pulse`}><span className="h-1.5 w-1.5 rounded-full bg-yellow-400"></span>分析中</span>;
      case 'failed':
        return <span className={`${baseClasses} bg-red-500/10 text-red-300`}><span className="h-1.5 w-1.5 rounded-full bg-red-400"></span>失败</span>;
      default:
        return <span className={`${baseClasses} bg-slate-500/10 text-slate-300`}><span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>未处理</span>;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen bg-slate-900">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500 mx-auto"></div>
            <p className="text-slate-300 text-lg mt-4">正在加载项目数据...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
          <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md w-full">
            <h3 className="text-2xl font-bold text-red-600 mb-4">糟糕，出错了！</h3>
            <p className="text-gray-600 mb-6">{error}</p>
            <button 
              onClick={fetchProjectData}
              className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700"
            >
              重试
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
          <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md w-full">
            <h3 className="text-2xl font-bold text-red-600 mb-4">未找到项目。</h3>
            <p className="text-gray-600 mb-6">请检查项目ID是否正确。</p>
            <button 
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700"
            >
              返回上一页
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={project?.name}>
      <div className="min-h-screen text-gray-800">
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          
          {/* Header */}
          <header className="flex flex-col sm:flex-row justify-between sm:items-center mb-8 gap-4">
            <div>
              <p className="text-sm text-blue-600 font-semibold">项目详情</p>
              <h1 className="text-3xl font-bold text-gray-900">{project?.name}</h1>
              <p className="text-gray-600 mt-1">{project?.description}</p>
            </div>
            <div className="flex items-center gap-3 self-start sm:self-center">
              <button 
                onClick={() => setUploadModalOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              >
                <PlusIcon className="h-5 w-5" />
                上传数据源
              </button>
            </div>
          </header>

          {/* Main Content Area */}
          <div className="space-y-8">
            {/* Semantic Search */}
            <ProjectSearch projectId={projectId} />
            
            {/* Data Sources Section */}
            <div>
              <div className="flex items-center gap-2 mb-6">
                <h3 className="text-xl font-bold text-gray-900">数据源列表</h3>
                <HelpTrigger
                  title="关于数据源"
                  content={
                    <div>
                      <p className="mb-2">数据源是您进行分析的基础。您可以上传多种格式的文件，例如：</p>
                      <ul className="list-disc list-inside space-y-1 pl-4 mb-4">
                        <li><b>表格文件 (.csv):</b> 将进行结构化数据探查，生成统计图表。</li>
                        <li><b>文本文件 (.txt):</b> 将进行深度文本分析，包括关键词提取、情感分析和摘要生成。</li>
                        <li><b>图片文件 (.jpg, .png):</b> 将进行图像分析，提取特征并支持相似图片查找。</li>
                      </ul>
                      <h4 className="font-semibold text-gray-800 mt-4 mb-2">💡 使用技巧</h4>
                      <ul className="list-disc list-inside space-y-1 pl-4">
                        <li><b>异步分析:</b> 数据分析是后台异步执行的。点击“查看与分析”后，您可以关闭页面或处理其他工作，稍后再回来查看已完成的分析报告。</li>
                        <li><b>语义搜索:</b> 上方的搜索框支持对所有数据源内容进行语义搜索，而不仅仅是文件名。</li>
                      </ul>
                    </div>
                  }
                />
              </div>
              {dataSources.length > 0 ? (
                 <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {dataSources.map(dataSource => (
                    <div
                      key={dataSource.id}
                      className="group rounded-lg bg-white border border-gray-200 shadow-sm p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-gray-300"
                    >
                      <div>
                        <div className="flex justify-between items-start mb-4">
                          <h4 className="text-lg font-bold text-gray-900 pr-4 break-all group-hover:text-blue-600 transition-colors">{dataSource.name}</h4>
                          {getStatusChip(dataSource.profiling_status)}
                        </div>
                        
                        <div className="mt-4 space-y-3 text-sm border-t border-gray-200 pt-4">
                          <div className="flex items-center justify-between text-gray-800">
                            <span className="flex items-center gap-2 text-gray-500"><TagIcon className="h-4 w-4"/>类型</span>
                                                            <span className="font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{dataSource.file_type || 'unknown'}</span>
                          </div>
                           <div className="flex items-center justify-between text-gray-800">
                            <span className="flex items-center gap-2 text-gray-500"><DatabaseIcon className="h-4 w-4"/>文件大小</span>
                            <span className="font-medium">{formatFileSize(dataSource.file_size || 0)}</span>
                          </div>
                          <div className="flex items-center justify-between text-gray-800">
                            <span className="flex items-center gap-2 text-gray-500"><ClockIcon className="h-4 w-4"/>上传时间</span>
                            <span className="font-medium text-xs">{formatDate(dataSource.uploaded_at || dataSource.created_at)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-6 flex items-center justify-end gap-3 border-t border-gray-200 pt-4">
                        <button 
                          onClick={() => navigate(`/project/${projectId}/data-source/${dataSource.id}`)}
                          className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-semibold hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200 flex items-center justify-center gap-2"
                        >
                          <ChartBarIcon className="h-4 w-4" />
                          查看与分析
                        </button>
                        <button
                          onClick={() => handleDeleteDataSource(dataSource.id)}
                          className="px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-md text-sm font-semibold hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors duration-200 flex items-center justify-center gap-2"
                        >
                           <TrashIcon className="h-4 w-4" />
                           删除
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 px-6 bg-white rounded-lg border border-dashed border-gray-300">
                   <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m2 5l-3.5-3.5M18 9.5A7.5 7.5 0 112.5 9.5A7.5 7.5 0 0118 9.5z" />
                   </svg>
                  <h3 className="mt-4 text-lg font-semibold text-gray-800">暂无数据源</h3>
                  <p className="mt-2 text-sm text-gray-600">
                    上传您的第一个数据源（如 .csv, .txt, .jpg）开始分析。
                  </p>
                   <button
                    onClick={() => setUploadModalOpen(true)}
                    className="mt-6 px-5 py-2.5 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700 flex items-center gap-2 mx-auto"
                  >
                    <PlusIcon className="h-5 w-5" />
                    上传第一个数据源
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <Modal
          isOpen={isUploadModalOpen}
          onClose={() => setUploadModalOpen(false)}
          title="上传新数据源"
        >
          <DataSourceUpload
            projectId={projectId}
            onSuccess={handleUploadSuccess}
            onClose={() => setUploadModalOpen(false)}
          />
        </Modal>
      </div>
    </Layout>
  );
};

export default ProjectDetailPage; 