import React, { useState } from 'react';
import Input from './Input';
import Button from './Button';
import { createProject } from '../services/api';

const CreateProjectForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 清除相应字段的错误
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = '项目名称不能为空';
    }
    
    if (!formData.description.trim()) {
      newErrors.description = '项目描述不能为空';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await createProject(formData);
      onSuccess(response.data);
    } catch (error) {
      console.error('创建项目失败:', error);
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail });
      } else {
        setErrors({ submit: '创建项目失败，请稍后重试' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="项目名称"
        name="name"
        value={formData.name}
        onChange={handleChange}
        error={errors.name}
        required
        placeholder="请输入项目名称"
      />
      
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          项目描述
          <span className="text-red-500 ml-1">*</span>
        </label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={4}
          className="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 px-3 py-2 text-sm"
          placeholder="请输入项目描述..."
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description}</p>
        )}
      </div>
      
      {errors.submit && (
        <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
          {errors.submit}
        </div>
      )}
      
      <div className="flex justify-end gap-3 pt-4">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
        >
          取消
        </Button>
        <Button
          type="submit"
          loading={loading}
        >
          创建项目
        </Button>
      </div>
    </form>
  );
};

export default CreateProjectForm; 