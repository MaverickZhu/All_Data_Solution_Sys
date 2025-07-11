import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as api from '../services/api';
import ProfilingReport from '../components/ProfilingReport';
import { useTaskPolling } from '../utils/useTaskPolling';
import Layout from '../components/Layout';
import Button from '../components/Button';
import { ArrowLeftIcon } from '@heroicons/react/24/solid';


const DataSourceDetail = () => {
    const { projectId, id: dataSourceId } = useParams(); 
    const navigate = useNavigate();
    
    const [dataSource, setDataSource] = useState(null);
    const [startError, setStartError] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    const { 
        taskStatus, 
        // taskResult, // Temporarily unused, will be used for rendering results later
        taskError, 
        startPolling, 
        resetTask 
    } = useTaskPolling();

    const fetchDataSource = useCallback(async () => {
        if (!projectId || !dataSourceId) return;
            setIsLoading(true);
            try {
                const response = await api.getDataSourceDetail(projectId, dataSourceId);
                setDataSource(response.data);
                if (response.data.task_id && (response.data.profile_status === 'in_progress' || response.data.profile_status === 'pending')) {
                    startPolling(response.data.task_id);
                }
            } catch (error) {
                console.error('Failed to fetch data source details:', error);
                setStartError('无法加载数据源详情。');
            } finally {
                setIsLoading(false);
            }
    }, [projectId, dataSourceId, startPolling]);

    useEffect(() => {
        fetchDataSource();
    }, [fetchDataSource]);

    useEffect(() => {
        if (taskStatus === 'completed') {
            const timer = setTimeout(() => {
                fetchDataSource();
            }, 1500); // Add a small delay to ensure backend has processed the result
            
            return () => clearTimeout(timer);
        }
    }, [taskStatus, fetchDataSource]);

    const handleStartProfiling = async () => {
        setStartError('');
        resetTask();
        try {
            const response = await api.startDataProfiling(dataSourceId, projectId);
            const newTaskId = response.data.task_id;
            if (newTaskId) {
                startPolling(newTaskId);
            } else {
                setStartError('未能从后端获取任务ID。');
            }
        } catch (error) {
            console.error('Failed to start data profiling:', error);
            setStartError(error.response?.data?.detail || '启动数据分析失败，请检查控制台获取详情。');
        }
    };
    
    const formatFileSize = (bytes) => {
        if (bytes === 0 || !bytes) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleString('zh-CN', { hour12: false });
    };

    const getStatusChip = (status) => {
        const baseClasses = "px-3 py-1 text-sm font-semibold rounded-full inline-flex items-center gap-2";
        switch (status) {
            case 'completed':
                return <span className={`${baseClasses} bg-green-500/10 text-green-300`}><span className="h-2 w-2 rounded-full bg-green-400"></span>已完成</span>;
            case 'in_progress':
                return <span className={`${baseClasses} bg-yellow-500/10 text-yellow-300 animate-pulse`}><span className="h-2 w-2 rounded-full bg-yellow-400"></span>分析中</span>;
            case 'failed':
                return <span className={`${baseClasses} bg-red-500/10 text-red-300`}><span className="h-2 w-2 rounded-full bg-red-400"></span>失败</span>;
            default:
                return <span className={`${baseClasses} bg-slate-500/10 text-slate-300`}><span className="h-2 w-2 rounded-full bg-slate-400"></span>未分析</span>;
        }
    };
    
    const reportData = dataSource?.profiling_result;

    if (isLoading) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-screen bg-slate-900">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500 mx-auto"></div>
                        <p className="text-slate-300 text-lg mt-4">加载数据源详情...</p>
                    </div>
                </div>
            </Layout>
        );
    }

    if (!dataSource) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-screen bg-slate-900 p-4">
                    <div className="text-center p-8 bg-slate-800/50 rounded-2xl shadow-xl">
                        <h3 className="text-xl font-semibold text-white mb-4">数据源未找到</h3>
                        <p className="text-slate-400 mb-6">请检查URL是否正确，或返回项目页重试。</p>
                        <Button onClick={() => navigate(`/project/${projectId}`)} variant="primary">
                            返回项目
                        </Button>
                    </div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title={`数据源: ${dataSource.name}`}>
            <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-200">
                <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
                    
                    {/* Header */}
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-white">{dataSource.name}</h1>
                        <Button 
                            onClick={() => navigate(`/project/${projectId}`)}
                            variant="secondary"
                            className="flex items-center gap-1.5 !px-3 !py-1.5"
                        >
                            <ArrowLeftIcon className="w-4 h-4" />
                            <span className="text-sm">返回</span>
                        </Button>
                    </div>

                    {/* Data Source Info Card */}
                    <div className="bg-black/20 backdrop-blur-md border border-white/10 shadow-lg rounded-2xl p-6">
                        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                            <div>
                                <h2 className="text-xl font-bold text-white">数据源概览</h2>
                                <p className="text-slate-400 mt-1">基本信息与分析状态</p>
                            </div>
                            {getStatusChip(dataSource.profile_status)}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 border-t border-white/10 pt-6">
                            <InfoItem label="数据源ID" value={dataSource.id} />
                            <InfoItem label="文件类型" value={dataSource.file_type?.toUpperCase() || 'UNKNOWN'} />
                            <InfoItem label="分析类别" value={dataSource.analysis_category || 'UNSTRUCTURED'} />
                            <InfoItem label="文件大小" value={formatFileSize(dataSource.file_size)} />
                            <InfoItem label="上传时间" value={formatDate(dataSource.uploaded_at || dataSource.created_at)} />
                        </div>
                    </div>

                    {/* Analysis Section */}
                    <div className="bg-black/20 backdrop-blur-md border border-white/10 shadow-lg rounded-2xl p-6">
                        <h3 className="text-xl font-bold text-white mb-4">智能分析</h3>
                        
                        {!reportData && (taskStatus !== 'in_progress' && taskStatus !== 'pending') && (
                            <div className="space-y-3 text-center py-8">
                                <p className="text-slate-300">此数据源尚未分析</p>
                            <Button 
                                onClick={handleStartProfiling} 
                                disabled={taskStatus === 'in_progress' || taskStatus === 'pending'}
                                    variant="primary"
                                    size="lg"
                            >
                                    立即开始分析
                            </Button>
                            </div>
                        )}
                        
                        {(taskStatus === 'in_progress' || taskStatus === 'pending') && (
                             <div className="flex flex-col items-center justify-center gap-4 p-8 bg-sky-500/10 rounded-lg border border-sky-500/20">
                                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sky-400"></div>
                                <div>
                                    <p className="text-sky-300 font-semibold text-center text-lg">分析进行中</p>
                                    <p className="text-sky-200 text-sm text-center mt-1">正在使用AI技术深度分析您的数据，请稍候...</p>
                                </div>
                            </div>
                        )}
                        
                        {startError && (
                            <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20 text-center">
                                <p className="text-red-300 font-semibold">启动失败</p>
                                <p className="text-red-200 text-sm mt-1">{startError}</p>
                            </div>
                        )}
                        
                        {taskError && (
                             <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20 text-center">
                                <p className="text-red-300 font-semibold">任务错误</p>
                                <p className="text-red-200 text-sm mt-1">{taskError}</p>
                            </div>
                        )}

                         {/* Analysis Results */}
                        {(taskStatus === 'completed' || reportData) && dataSource.profiling_result && (
                            <ProfilingReport report={dataSource.profiling_result} dataSource={dataSource} />
                        )}
                    </div>

                </div>
                </div>
        </Layout>
    );
};

const InfoItem = ({ label, value }) => (
    <div className="bg-slate-800/30 p-4 rounded-lg">
        <div className="text-sm text-slate-400 mb-1">{label}</div>
        <div className="font-semibold text-white truncate">{value}</div>
    </div>
);

export default DataSourceDetail; 