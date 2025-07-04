import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from './Card';
import Button from './Button';

const ProjectCard = ({ project, onDelete }) => {
  const navigate = useNavigate();
  
  const handleViewProject = () => {
    navigate(`/projects/${project.id}`);
  };
  
  const handleDeleteProject = () => {
    if (window.confirm(`确定要删除项目 "${project.name}" 吗？此操作不可恢复。`)) {
      onDelete(project.id);
    }
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
    <Card
      hover
      className="h-full"
      title={project.name}
      subtitle={project.description}
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleViewProject}
          >
            查看
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleDeleteProject}
          >
            删除
          </Button>
        </div>
      }
    >
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">状态</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
            {getStatusText(project.status)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">创建时间</span>
          <span className="text-sm text-gray-900">{formatDate(project.created_at)}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">更新时间</span>
          <span className="text-sm text-gray-900">{formatDate(project.updated_at)}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">数据源</span>
          <span className="text-sm text-gray-900">
            {project.data_sources?.length || 0} 个
          </span>
        </div>
      </div>
    </Card>
  );
};

export default ProjectCard; 