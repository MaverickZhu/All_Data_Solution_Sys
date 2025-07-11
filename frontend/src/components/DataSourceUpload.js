import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDataSource } from '../services/api';

const DataSourceUpload = ({ projectId, onSuccess, onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxFiles: 1,
    maxSize: 200 * 1024 * 1024, // 200MB
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDataSource(projectId, file);
      onSuccess(); // Callback on successful upload
    } catch (err) {
      console.error("Upload failed", err);
      setError('文件上传失败，请重试。');
    } finally {
      setUploading(false);
    }
  };
  
  const baseDropzoneClass = "flex flex-col items-center justify-center w-full h-64 rounded-lg border-2 border-dashed transition-all duration-300 cursor-pointer";
  const inactiveDropzoneClass = "border-gray-300 bg-gray-50 hover:bg-gray-100";
  const activeDropzoneClass = "border-blue-500 bg-blue-50";

  return (
    <div className="flex flex-col gap-4 text-gray-800">
      <div {...getRootProps()} className={`${baseDropzoneClass} ${isDragActive ? activeDropzoneClass : inactiveDropzoneClass}`}>
        <input {...getInputProps()} />
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="mt-4 text-sm text-gray-600">
            {isDragActive ? '将文件拖放到此处...' : '将文件拖到此处，或点击选择文件'}
          </p>
          <p className="text-xs text-gray-500 mt-1">支持 DOCX, PDF, MD, TXT, CSV, JPG, PNG (最大 200MB)</p>
        </div>
      </div>

      {file && (
        <div className="text-center p-2 bg-gray-100 rounded-md">
          <p className="text-sm font-medium text-gray-700 truncate">已选择: {file.name}</p>
        </div>
      )}
      
      {error && (
        <div className="text-center p-2 bg-red-100 rounded-md">
            <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}

      <div className="flex justify-end gap-4 mt-2">
        <button 
          onClick={onClose} 
          className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          取消
        </button>
        <button 
          onClick={handleUpload} 
          disabled={!file || uploading}
          className="px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          {uploading && (
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {uploading ? '上传中...' : '确认上传'}
        </button>
      </div>
    </div>
  );
};

export default DataSourceUpload; 