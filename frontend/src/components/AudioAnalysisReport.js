import React from 'react';

const StatCard = ({ label, value, icon, className = '' }) => (
    <div className={`bg-slate-800/50 p-4 rounded-lg flex items-center gap-4 ${className}`}>
        {icon && <div className="text-sky-400 text-2xl">{icon}</div>}
        <div>
            <div className="text-sm text-slate-400">{label}</div>
            <div className="text-lg font-bold text-white truncate">{value ?? 'N/A'}</div>
        </div>
    </div>
);

const MetadataCard = ({ title, data }) => (
    <div className="bg-slate-800/50 p-4 rounded-lg">
        <h5 className="text-sm font-medium text-sky-400 mb-3">{title}</h5>
        <div className="space-y-2 max-h-32 overflow-y-auto">
            {Object.entries(data || {}).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                    <span className="text-slate-400 truncate mr-2">{key}:</span>
                    <span className="text-white text-right">{value || 'N/A'}</span>
                </div>
            ))}
        </div>
    </div>
);

const AudioAnalysisReport = ({ result }) => {


    if (!result || result.analysis_type !== 'audio') {
        return <div className="text-center text-slate-400 py-10">音频分析数据不可用或格式错误。</div>;
    }

    const { file_info, metadata, audio_properties, analysis_summary, ai_analysis } = result;
    const hasError = result.error;

    if (hasError) {
        return (
            <div className="text-center text-red-400 py-10">
                <div className="text-6xl mb-4">⚠️</div>
                <div>音频分析失败</div>
                <div className="text-sm text-slate-400 mt-2">{result.error}</div>
            </div>
        );
    }

    // 格式化时长
    const formatDuration = (seconds) => {
        if (!seconds || seconds === 0) return 'N/A';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}分${secs}秒`;
    };

    // 格式化比特率
    const formatBitrate = (bitrate) => {
        if (!bitrate || bitrate === 0) return 'N/A';
        return `${bitrate} kbps`;
    };

    // 格式化采样率
    const formatSampleRate = (sampleRate) => {
        if (!sampleRate || sampleRate === 0) return 'N/A';
        return `${sampleRate} Hz`;
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 text-slate-200">
            {/* Left Column: Audio Icon and Basic Info */}
            <div className="lg:col-span-1 space-y-6">
                <div className="bg-black/20 p-8 rounded-2xl border border-white/10 text-center">
                    <div className="text-8xl mb-4">🎵</div>
                    <div className="text-lg font-semibold text-white">
                        {file_info?.format?.toUpperCase() || 'AUDIO'} 文件
                    </div>
                    <div className="text-sm text-slate-400 mt-2">
                        {analysis_summary?.file_size_mb} MB
                    </div>
                </div>

                {/* Basic Audio Properties */}
                <div className="grid grid-cols-1 gap-4">
                    <StatCard 
                        label="时长" 
                        value={formatDuration(analysis_summary?.total_duration)} 
                        icon="⏱️"
                    />
                    <StatCard 
                        label="音频质量" 
                        value={analysis_summary?.audio_quality} 
                        icon="🎧"
                    />
                    <StatCard 
                        label="音频类型" 
                        value={analysis_summary?.audio_type} 
                        icon="🎼"
                    />
                </div>
            </div>

            {/* Right Column: Detailed Analysis */}
            <div className="lg:col-span-2 space-y-6">
                {/* Audio Properties */}
                <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 p-6 rounded-2xl border border-purple-500/20">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="text-2xl">🔊</span>
                        音频属性
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <StatCard 
                            label="比特率" 
                            value={formatBitrate(audio_properties?.bitrate)}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="采样率" 
                            value={formatSampleRate(audio_properties?.sample_rate)}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="声道数" 
                            value={audio_properties?.channels || 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="节拍" 
                            value={audio_properties?.tempo_bpm ? `${Math.round(audio_properties.tempo_bpm)} BPM` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="频谱质心" 
                            value={audio_properties?.spectral_centroid_mean ? `${Math.round(audio_properties.spectral_centroid_mean)} Hz` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="能量" 
                            value={audio_properties?.energy ? audio_properties.energy.toFixed(4) : 'N/A'}
                            className="bg-black/30"
                        />
                    </div>
                </div>

                {/* Metadata */}
                {metadata && Object.keys(metadata).length > 0 && (
                    <div className="bg-gradient-to-r from-green-900/20 to-teal-900/20 p-6 rounded-2xl border border-green-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">📋</span>
                            音频元数据
                        </h4>
                        <div className="bg-slate-800/50 p-4 rounded-lg">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* 基础信息 */}
                                <div>
                                    <h5 className="text-sm font-medium text-sky-400 mb-2">基础信息</h5>
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">文件格式:</span>
                                            <span className="text-white">{file_info?.format?.toUpperCase() || 'N/A'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">文件大小:</span>
                                            <span className="text-white">{analysis_summary?.file_size_mb ? `${analysis_summary.file_size_mb} MB` : 'N/A'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">时长:</span>
                                            <span className="text-white">{formatDuration(analysis_summary?.total_duration)}</span>
                                        </div>
                                    </div>
                                </div>
                                {/* 技术参数 */}
                                <div>
                                    <h5 className="text-sm font-medium text-sky-400 mb-2">技术参数</h5>
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">比特率:</span>
                                            <span className="text-white">{formatBitrate(audio_properties?.bitrate)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">采样率:</span>
                                            <span className="text-white">{formatSampleRate(audio_properties?.sample_rate)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">音频质量:</span>
                                            <span className="text-white">{analysis_summary?.audio_quality || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Audio Features (MFCC) */}
                {audio_properties?.mfcc_means && (
                    <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 p-6 rounded-2xl border border-orange-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">📊</span>
                            音频特征分析
                        </h4>
                        <div className="bg-black/30 p-4 rounded-lg">
                            <h5 className="text-sm font-medium text-sky-400 mb-2">MFCC 特征</h5>
                            <div className="grid grid-cols-4 md:grid-cols-6 gap-2">
                                {audio_properties.mfcc_means.slice(0, 12).map((value, index) => (
                                    <div key={index} className="text-center">
                                        <div className="text-xs text-slate-400">C{index + 1}</div>
                                        <div className="text-sm font-mono text-white">
                                            {value.toFixed(2)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="text-xs text-slate-400 mt-2">
                                MFCC (梅尔频率倒谱系数) 用于描述音频的频谱特征
                            </div>
                        </div>
                    </div>
                )}

                {/* AI Analysis Results */}
                {ai_analysis && ai_analysis.ai_description && (
                    <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 p-6 rounded-2xl border border-purple-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">🤖</span>
                            AI智能分析
                        </h4>
                        
                        {/* AI Description */}
                        <div className="bg-slate-800/50 p-4 rounded-lg mb-4">
                            <h5 className="text-sm font-medium text-sky-400 mb-2">智能内容分析</h5>
                            <p className="text-slate-200 text-sm leading-relaxed">
                                {ai_analysis.ai_description}
                            </p>
                        </div>

                        {/* AI Analysis Results Grid */}
                        {ai_analysis.ai_analysis && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Audio Type Classification */}
                                {ai_analysis.ai_audio_type && (
                                    <div className="bg-slate-800/50 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">音频类型</h5>
                                        <div className="flex items-center gap-2">
                                            <span className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 rounded text-blue-300 text-sm">
                                                {ai_analysis.ai_audio_type}
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Quality Assessment */}
                                {ai_analysis.ai_quality_assessment && (
                                    <div className="bg-slate-800/50 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">质量评估</h5>
                                        <div className="flex items-center gap-2">
                                            <span className={`px-2 py-1 rounded text-sm ${
                                                ai_analysis.ai_quality_assessment.includes('高') ? 'bg-green-500/20 border border-green-500/30 text-green-300' :
                                                ai_analysis.ai_quality_assessment.includes('良') ? 'bg-yellow-500/20 border border-yellow-500/30 text-yellow-300' :
                                                'bg-orange-500/20 border border-orange-500/30 text-orange-300'
                                            }`}>
                                                {ai_analysis.ai_quality_assessment}
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Feature Tags */}
                                {ai_analysis.ai_feature_tags && ai_analysis.ai_feature_tags.length > 0 && (
                                    <div className="bg-slate-800/50 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">音频特征</h5>
                                        <div className="flex flex-wrap gap-2">
                                            {ai_analysis.ai_feature_tags.map((tag, index) => (
                                                <span key={index} className="px-2 py-1 bg-purple-500/20 border border-purple-500/30 rounded text-purple-300 text-xs">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Usage Scenarios */}
                                {ai_analysis.ai_usage_scenarios && ai_analysis.ai_usage_scenarios.length > 0 && (
                                    <div className="bg-slate-800/50 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">适用场景</h5>
                                        <div className="space-y-1">
                                            {ai_analysis.ai_usage_scenarios.map((scenario, index) => (
                                                <div key={index} className="text-slate-300 text-sm flex items-center gap-2">
                                                    <span className="text-sky-400">•</span>
                                                    {scenario}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* AI Error Handling */}
                        {ai_analysis.ai_error && (
                            <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-amber-400">⚠️</span>
                                    <span className="text-amber-300 font-semibold">AI分析遇到问题</span>
                                </div>
                                <p className="text-amber-200 text-sm">
                                    {ai_analysis.ai_error}
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Analysis Summary */}
                <div className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 p-6 rounded-2xl border border-indigo-500/20">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="text-2xl">📝</span>
                        分析总结
                    </h4>
                    <div className="space-y-3">
                        <div className="bg-black/30 p-4 rounded-lg">
                            <h5 className="text-sm font-medium text-sky-400 mb-2">基本信息</h5>
                            <p className="text-white">
                                这是一个 {analysis_summary?.format_info} 的{analysis_summary?.audio_type}，
                                时长为 {formatDuration(analysis_summary?.total_duration)}，
                                文件大小为 {analysis_summary?.file_size_mb} MB，
                                音频质量为{analysis_summary?.audio_quality}。
                            </p>
                        </div>
                        
                        {audio_properties?.tempo_bpm && (
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-sky-400 mb-2">节奏分析</h5>
                                <p className="text-white">
                                    检测到的节拍为 {Math.round(audio_properties.tempo_bpm)} BPM，
                                    {audio_properties.tempo_bpm > 120 ? '属于快节奏音频' : 
                                     audio_properties.tempo_bpm > 80 ? '属于中等节奏音频' : '属于慢节奏音频'}。
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AudioAnalysisReport; 