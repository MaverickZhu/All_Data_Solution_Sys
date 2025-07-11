import React, { memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { EyeIcon, TrashIcon } from '@heroicons/react/24/solid';

const ProjectCard = ({ project, onDelete }) => {
  const navigate = useNavigate();
  
  const handleViewProject = () => {
    navigate(`/project/${project.id}`);
  };
  
  const handleDeleteProject = () => {
    onDelete(project.id);
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('zh-CN');
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'on_hold':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusText = (status) => {
    switch (status) {
      case 'active':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'on_hold':
        return '暂停';
      default:
        return '未知';
    }
  };
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 h-full flex flex-col transition-all duration-300 hover:shadow-lg hover:border-gray-300">
      <div className="flex-grow">
        <h3 className="text-lg font-bold text-gray-900 truncate">{project.name}</h3>
        <p className="text-gray-600 text-sm mt-1 mb-6 min-h-[40px]">{project.description}</p>
      
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">状态</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
              {getStatusText(project.status)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">创建时间</span>
            <span className="text-gray-800 font-mono">{formatDate(project.created_at)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">更新时间</span>
            <span className="text-gray-800 font-mono">{formatDate(project.updated_at)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">数据源</span>
            <span className="text-gray-800 font-mono">
              {project.data_sources?.length || 0} 个
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 flex justify-end gap-3">
        <button
          onClick={handleViewProject}
          className="project-card-view-button px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <EyeIcon className="h-4 w-4" />
          查看
        </button>
        <button
          onClick={handleDeleteProject}
          className="project-card-delete-button px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-md text-sm font-semibold hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <TrashIcon className="h-4 w-4" />
          删除
        </button>
      </div>
    </div>
  );
};

export default memo(ProjectCard); 