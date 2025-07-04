import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Card from '../components/Card';
import { getProject, getDataSources, uploadDataSource, deleteDataSource } from '../services/api';

const ProjectDetailPage = () => {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [dataSources, setDataSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const fetchProjectData = useCallback(async () => {
    try {
      setLoading(true);
      const [projectResponse, dataSourcesResponse] = await Promise.all([
        getProject(id),
        getDataSources(id)
      ]);
      
      setProject(projectResponse.data);
      setDataSources(dataSourcesResponse.data);
      setError(null);
    } catch (err) {
      console.error('获取项目数据失败:', err);
      setError('获取项目数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadError('');

    try {
      const response = await uploadDataSource(id, file);
      setDataSources(prev => [...prev, response.data]);
      setShowUploadModal(false);
    } catch (err) {
      console.error('上传文件失败:', err);
      setUploadError(err.response?.data?.detail || '上传文件失败，请稍后重试');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDataSource = async (dataSourceId) => {
    if (!window.confirm('确定要删除这个数据源吗？此操作不可恢复。')) {
      return;
    }

    try {
      await deleteDataSource(id, dataSourceId);
      setDataSources(prev => prev.filter(ds => ds.id !== dataSourceId));
    } catch (err) {
      console.error('删除数据源失败:', err);
      alert('删除数据源失败，请稍后重试');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">加载中...</span>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="text-red-600 mb-4">{error}</div>
          <Button onClick={fetchProjectData}>重试</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={project?.name}>
      <div className="space-y-6">
        {/* 项目信息卡片 */}
        <Card title="项目信息">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">项目描述</h4>
              <p className="text-gray-600">{project?.description || '暂无描述'}</p>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-500">状态:</span>
                <span className="font-medium">{project?.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">创建时间:</span>
                <span className="font-medium">{formatDate(project?.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">更新时间:</span>
                <span className="font-medium">{formatDate(project?.updated_at)}</span>
              </div>
            </div>
          </div>
        </Card>

        {/* 数据源管理 */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">数据源管理</h3>
            <Button onClick={() => setShowUploadModal(true)}>
              上传数据源
            </Button>
          </div>

          {dataSources.length === 0 ? (
            <Card>
              <div className="text-center py-8">
                <svg 
                  className="mx-auto h-12 w-12 text-gray-400" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" 
                  />
                </svg>
                <h4 className="mt-2 text-sm font-medium text-gray-900">暂无数据源</h4>
                <p className="mt-1 text-sm text-gray-500">
                  上传您的数据文件开始分析
                </p>
                <div className="mt-4">
                  <Button onClick={() => setShowUploadModal(true)}>
                    上传数据源
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {dataSources.map(dataSource => (
                <Card
                  key={dataSource.id}
                  hover
                  title={dataSource.name}
                  subtitle={dataSource.type}
                  actions={
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDeleteDataSource(dataSource.id)}
                    >
                      删除
                    </Button>
                  }
                >
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">文件大小:</span>
                      <span className="text-sm">{formatFileSize(dataSource.size || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">上传时间:</span>
                      <span className="text-sm">{formatDate(dataSource.created_at)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">状态:</span>
                      <span className="text-sm">{dataSource.status || '就绪'}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* 上传数据源模态框 */}
        <Modal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          title="上传数据源"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择文件
              </label>
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                accept=".csv,.xlsx,.xls,.json,.txt"
              />
              <p className="mt-1 text-xs text-gray-500">
                支持 CSV, Excel, JSON, TXT 格式文件
              </p>
            </div>

            {uploadError && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
                {uploadError}
              </div>
            )}

            {uploading && (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">上传中...</span>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => setShowUploadModal(false)}
                disabled={uploading}
              >
                取消
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </Layout>
  );
};

export default ProjectDetailPage; 