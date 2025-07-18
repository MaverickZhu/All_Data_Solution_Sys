import React, { useState, useEffect, useMemo } from 'react';

const VideoDeepAnalysisProgress = ({ analysisId, onComplete, onError }) => {
    const [progress, setProgress] = useState({
        status: 'PENDING',
        phase: '准备中',
        progress: 0,
        attempts: 0,
        maxAttempts: 120, // 更新为120次
        processing_time: 0,
        error_message: null
    });

    const [phaseDetails, setPhaseDetails] = useState({
        current_phase: '初始化',
        completed_phases: [],
        estimated_total_time: 600 // 10分钟预估
    });

    // 阶段映射 - 使用useMemo避免重新创建
    const phaseMap = useMemo(() => ({
        'PENDING': { name: '准备中', icon: '⏳', description: '正在初始化分析环境...' },
        'IN_PROGRESS': { name: '分析中', icon: '🔄', description: '正在进行多模态分析...' },
        'COMPLETED': { name: '完成', icon: '✅', description: '深度分析已完成！' },
        'FAILED': { name: '失败', icon: '❌', description: '分析过程中出现错误' }
    }), []);

    // 分析阶段详情 - 使用useMemo避免重新创建
    const analysisPhases = useMemo(() => [
        { id: 'initialization', name: '初始化', icon: '🚀', description: '准备分析环境和模型' },
        { id: 'frame_extraction', name: '关键帧提取', icon: '🎬', description: '智能提取视频关键帧' },
        { id: 'visual_analysis', name: '视觉分析', icon: '👁️', description: 'AI视觉语义理解' },
        { id: 'audio_extraction', name: '音频提取', icon: '🎵', description: '提取和预处理音频' },
        { id: 'speech_recognition', name: '语音识别', icon: '🗣️', description: 'Whisper语音转文字' },
        { id: 'audio_semantics', name: '音频语义', icon: '🧠', description: '音频内容语义分析' },
        { id: 'multimodal_fusion', name: '多模态融合', icon: '🔗', description: '视觉+音频语义融合' },
        { id: 'story_analysis', name: '故事分析', icon: '📖', description: '情节和关键时刻识别' },
        { id: 'finalization', name: '结果整理', icon: '📊', description: '生成综合分析报告' }
    ], []);

    useEffect(() => {
        if (!analysisId) return;

        const pollStatus = async () => {
            try {
                const { pollVideoAnalysisStatus } = await import('../services/api');
                
                const result = await pollVideoAnalysisStatus(
                    analysisId,
                    (progressData) => {
                        setProgress(prev => ({
                            ...prev,
                            ...progressData,
                            phase: phaseMap[progressData.status]?.name || '处理中'
                        }));

                        // 使用后端返回的真实进度数据
                        let actualProgress = progressData.progress_percentage || progressData.progress || 0;
                        
                        // 如果后端没有提供进度，根据任务状态估算
                        if (!progressData.progress_percentage && !progressData.progress) {
                            if (progressData.status === 'PENDING') {
                                actualProgress = 5;
                            } else if (progressData.status === 'IN_PROGRESS') {
                                // 基于处理时间估算进度（假设总共需要8-10分钟）
                                const processingTime = progressData.processing_time || 0;
                                const estimatedTotalTime = 600; // 10分钟
                                actualProgress = Math.min(10 + (processingTime / estimatedTotalTime) * 80, 90);
                            } else if (progressData.status === 'COMPLETED') {
                                actualProgress = 100;
                            }
                        }

                        // 更新阶段信息 - 优先使用后端提供的阶段信息
                        const currentPhaseIndex = Math.floor((actualProgress / 100) * analysisPhases.length);
                        const estimatedPhase = analysisPhases[Math.min(currentPhaseIndex, analysisPhases.length - 1)];
                        const currentPhaseName = progressData.current_phase || progressData.progress_message || estimatedPhase.name;
                        
                        setPhaseDetails(prev => ({
                            ...prev,
                            current_phase: currentPhaseName,
                            completed_phases: analysisPhases.slice(0, currentPhaseIndex).map(p => p.id),
                            actual_progress: actualProgress
                        }));
                    }
                );

                if (result.status === 'completed') {
                    setProgress(prev => ({ ...prev, progress: 100, status: 'COMPLETED' }));
                    setPhaseDetails(prev => ({
                        ...prev,
                        current_phase: '完成',
                        completed_phases: analysisPhases.map(p => p.id)
                    }));
                    onComplete && onComplete(result.data);
                } else if (result.status === 'failed' || result.status === 'error' || result.status === 'timeout') {
                    setProgress(prev => ({ 
                        ...prev, 
                        status: 'FAILED', 
                        error_message: result.error 
                    }));
                    onError && onError(result.error);
                }
            } catch (error) {
                // 仅在开发环境显示详细错误
                if (process.env.NODE_ENV === 'development') {
                    console.error('轮询状态失败:', error);
                }
                setProgress(prev => ({ 
                    ...prev, 
                    status: 'FAILED', 
                    error_message: '网络连接错误' 
                }));
                onError && onError('网络连接错误');
            }
        };

        pollStatus();
    }, [analysisId, analysisPhases, phaseMap, onComplete, onError]);

    const currentPhaseInfo = phaseMap[progress.status] || phaseMap['PENDING'];
    
    // 计算实际显示的进度 - 优先使用后端真实进度
    let displayProgress = phaseDetails.actual_progress || progress.progress_percentage || progress.progress || 0;
    
    // 如果没有真实进度数据，使用状态估算
    if (!displayProgress || displayProgress === 0) {
        if (progress.status === 'PENDING') {
            displayProgress = 5;
        } else if (progress.status === 'IN_PROGRESS') {
            const processingTime = progress.processing_time || 0;
            const estimatedTotalTime = 600; // 10分钟
            displayProgress = Math.min(10 + (processingTime / estimatedTotalTime) * 80, 90);
        } else if (progress.status === 'COMPLETED') {
            displayProgress = 100;
        }
    }

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
            {/* 主标题 */}
            <div className="flex items-center gap-3 mb-6">
                <div className="text-2xl animate-spin">{currentPhaseInfo.icon}</div>
                <div>
                    <h3 className="text-xl font-bold text-white">🧠 视频深度分析进行中</h3>
                    <p className="text-slate-300 text-sm">{currentPhaseInfo.description}</p>
                </div>
            </div>

            {/* 总体进度条 */}
            <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-slate-300">总体进度</span>
                    <span className="text-sm text-sky-400">{displayProgress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                    <div 
                        className="bg-gradient-to-r from-sky-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${displayProgress}%` }}
                    ></div>
                </div>
            </div>

            {/* 当前阶段信息 */}
            <div className="mb-6 p-4 bg-sky-500/10 rounded-lg border border-sky-500/20">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">🔄</span>
                    <span className="font-semibold text-sky-300">当前阶段: {phaseDetails.current_phase}</span>
                </div>
                <p className="text-sm text-slate-300">
                    {analysisPhases.find(p => p.name === phaseDetails.current_phase)?.description || '正在处理...'}
                </p>
            </div>

            {/* 分析阶段列表 */}
            <div className="space-y-2">
                <h4 className="text-sm font-medium text-slate-300 mb-3">分析阶段</h4>
                {analysisPhases.map((phase) => {
                    const isCompleted = phaseDetails.completed_phases.includes(phase.id);
                    const isCurrent = phase.name === phaseDetails.current_phase;

                    return (
                        <div 
                            key={phase.id}
                            className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                                isCompleted ? 'bg-green-500/10 border border-green-500/20' :
                                isCurrent ? 'bg-sky-500/10 border border-sky-500/20 animate-pulse' :
                                'bg-slate-700/30'
                            }`}
                        >
                            <span className="text-lg">
                                {isCompleted ? '✅' : isCurrent ? '🔄' : phase.icon}
                            </span>
                            <div className="flex-1">
                                <span className={`text-sm font-medium ${
                                    isCompleted ? 'text-green-300' :
                                    isCurrent ? 'text-sky-300' :
                                    'text-slate-400'
                                }`}>
                                    {phase.name}
                                </span>
                                <p className={`text-xs ${
                                    isCompleted ? 'text-green-400' :
                                    isCurrent ? 'text-sky-400' :
                                    'text-slate-500'
                                }`}>
                                    {phase.description}
                                </p>
                            </div>
                            {isCompleted && <span className="text-green-400 text-xs">完成</span>}
                            {isCurrent && <span className="text-sky-400 text-xs">进行中</span>}
                        </div>
                    );
                })}
            </div>

            {/* 状态信息 */}
            <div className="mt-6 pt-4 border-t border-slate-700">
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span className="text-slate-400">进度详情:</span>
                        <span className="text-white ml-2">
                            {progress.progress_message || `${displayProgress.toFixed(1)}% 完成`}
                        </span>
                    </div>
                    <div>
                        <span className="text-slate-400">处理时间:</span>
                        <span className="text-white ml-2">{Math.floor(progress.processing_time || 0)}秒</span>
                    </div>
                    <div>
                        <span className="text-slate-400">当前阶段:</span>
                        <span className="text-white ml-2">{progress.current_phase || phaseDetails.current_phase}</span>
                    </div>
                    <div>
                        <span className="text-slate-400">轮询状态:</span>
                        <span className="text-white ml-2">{progress.attempts}/{progress.maxAttempts}</span>
                    </div>
                </div>
                
                {progress.error_message && (
                    <div className="mt-3 p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                        <div className="flex items-center gap-2">
                            <span className="text-red-400">❌</span>
                            <span className="text-red-300 text-sm font-medium">错误信息</span>
                        </div>
                        <p className="text-red-200 text-sm mt-1">{progress.error_message}</p>
                    </div>
                )}
            </div>

            {/* 预计完成时间 */}
            <div className="mt-4 text-center">
                <p className="text-xs text-slate-400">
                    预计总用时: {Math.floor(phaseDetails.estimated_total_time / 60)}分{phaseDetails.estimated_total_time % 60}秒
                </p>
                <p className="text-xs text-slate-500 mt-1">
                    💡 深度分析利用AI模型进行多模态语义理解，请耐心等待
                </p>
                {progress.attempts > 60 && progress.status === 'IN_PROGRESS' && (
                    <div className="mt-2 p-2 bg-yellow-500/10 rounded border border-yellow-500/20">
                        <p className="text-xs text-yellow-300">
                            ⏰ 分析时间较长，这是正常现象。复杂视频需要更多处理时间。
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default VideoDeepAnalysisProgress; 