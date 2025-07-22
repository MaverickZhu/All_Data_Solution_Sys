import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as api from '../services/api';
import ProfilingReport from '../components/ProfilingReport';
import VideoAnalysisReport from '../components/VideoAnalysisReport';
import VideoDeepAnalysisProgress from '../components/VideoDeepAnalysisProgress';
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
    
    // 视频深度分析相关状态
    const [videoAnalysisId, setVideoAnalysisId] = useState(null);
    const [showVideoProgress, setShowVideoProgress] = useState(false);
    const [videoAnalysisResult, setVideoAnalysisResult] = useState(null);

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
                
                // 如果是视频文件，尝试获取视频分析数据
                if (response.data.analysis_category === 'VIDEO') {
                    try {
                        const videoAnalysisResponse = await api.getVideoAnalysisStatusByDataSource(dataSourceId);
                        if (videoAnalysisResponse.data) {
                            console.log('Video analysis response:', videoAnalysisResponse.data);
                            
                            // 检查是否有完整的分析结果
                            if (videoAnalysisResponse.data.analysis_result) {
                                setVideoAnalysisResult(videoAnalysisResponse.data.analysis_result);
                                console.log('Video analysis result loaded:', videoAnalysisResponse.data.analysis_result);
                            } else {
                                console.log('Video analysis status:', videoAnalysisResponse.data.status);
                                // 如果没有结果但状态是完成，显示警告
                                if (videoAnalysisResponse.data.status === 'COMPLETED') {
                                    console.warn('Video analysis is COMPLETED but no analysis_result found');
                                }
                            }
                        }
                    } catch (videoError) {
                        console.error('Failed to fetch video analysis result:', videoError);
                        // 视频分析结果获取失败不影响主要功能，继续正常流程
                    }
                }
                
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

    const handleVideoDeepAnalysis = async () => {
        setStartError('');
        resetTask();
        try {
            const response = await api.startVideoDeepAnalysis(dataSourceId);
            // console.log('视频深度分析响应:', response.data);
            const analysisId = response.data.id || response.data.analysis_id;
            if (analysisId) {
                // 设置分析ID并显示进度组件
                setVideoAnalysisId(analysisId);
                setShowVideoProgress(true);
                // console.log('视频深度分析已启动，分析ID:', analysisId);
            } else {
                // console.log('响应中没有找到分析ID:', response.data);
                setStartError('未能启动视频深度分析。');
            }
        } catch (error) {
            console.error('Failed to start video deep analysis:', error);
            setStartError(error.response?.data?.detail || '启动视频深度分析失败，请检查控制台获取详情。');
        }
    };

    const handleVideoAnalysisComplete = (result) => {
        // console.log('视频深度分析完成:', result);
        setShowVideoProgress(false);
        setVideoAnalysisId(null);
        
        // 刷新数据源信息
        setTimeout(() => {
            fetchDataSource();
        }, 1000);
        
        // 显示成功提示
        alert('🎉 视频深度分析完成！\n\n分析结果已保存，页面将自动刷新显示详细报告。');
    };

    const handleVideoAnalysisError = (error) => {
        console.error('视频深度分析失败:', error);
        setShowVideoProgress(false);
        setVideoAnalysisId(null);
        setStartError(`视频深度分析失败: ${error}`);
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
    
    // 智能解析profiling_result（支持JSON字符串和对象）
    const reportData = dataSource?.profiling_result ? 
        (typeof dataSource.profiling_result === 'string' ? 
            JSON.parse(dataSource.profiling_result) : 
            dataSource.profiling_result) : 
        null;

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
                        
                        {reportData && (taskStatus !== 'in_progress' && taskStatus !== 'pending') && (
                            <div className="flex justify-between items-center mb-4">
                                <div className="flex items-center gap-2">
                                    <span className="h-2 w-2 rounded-full bg-green-400"></span>
                                    <span className="text-green-300 font-medium">分析已完成</span>
                                </div>
                                <div className="flex gap-2">
                                    {/* 视频深度分析按钮 */}
                                    {dataSource.analysis_category === 'VIDEO' && (
                                        <Button 
                                            onClick={handleVideoDeepAnalysis} 
                                            disabled={taskStatus === 'in_progress' || taskStatus === 'pending' || showVideoProgress}
                                            variant="primary"
                                            size="sm"
                                        >
                                            🧠 深度分析
                                        </Button>
                                    )}
                                    <Button 
                                        onClick={handleStartProfiling} 
                                        disabled={taskStatus === 'in_progress' || taskStatus === 'pending'}
                                        variant="secondary"
                                        size="sm"
                                    >
                                        🔄 重新分析
                                    </Button>
                                </div>
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

                        {/* Video Deep Analysis Progress */}
                        {showVideoProgress && videoAnalysisId && (
                            <VideoDeepAnalysisProgress
                                analysisId={videoAnalysisId}
                                onComplete={handleVideoAnalysisComplete}
                                onError={handleVideoAnalysisError}
                            />
                        )}

                        {/* Video Deep Analysis Results (视频类型专用显示) */}
                        {dataSource?.analysis_category === 'VIDEO' && videoAnalysisResult && !showVideoProgress && (
                            <VideoAnalysisReport result={videoAnalysisResult} filePath={dataSource?.file_path} />
                        )}
                        
                        {/* Regular Analysis Results (非视频类型显示，或视频类型无深度分析结果时显示) */}
                        {(taskStatus === 'completed' || reportData) && reportData && !showVideoProgress && 
                         !(dataSource?.analysis_category === 'VIDEO' && videoAnalysisResult) && (
                            <ProfilingReport report={reportData} dataSource={dataSource} />
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