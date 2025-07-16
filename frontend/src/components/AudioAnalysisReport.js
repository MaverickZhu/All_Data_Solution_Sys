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

    const { file_info, metadata, audio_properties, analysis_summary, speech_recognition } = result;
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

                {/* Speech Recognition Results */}
                {speech_recognition && (
                    <div className="bg-gradient-to-r from-green-900/20 to-teal-900/20 p-6 rounded-2xl border border-green-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">🎤</span>
                            语音识别结果
                        </h4>
                        
                        {speech_recognition.success ? (
                            <div className="space-y-4">
                                {/* Transcribed Text */}
                                {speech_recognition.transcribed_text && (
                                    <div className="bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-green-400 mb-2">转录文本</h5>
                                        <p className="text-slate-200 text-sm italic leading-relaxed border-l-2 border-green-500/30 pl-3">
                                            "{speech_recognition.transcribed_text}"
                                        </p>
                                    </div>
                                )}
                                
                                {/* Recognition Details */}
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                    {speech_recognition.confidence !== undefined && (
                                        <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400 mb-1">识别置信度</div>
                                            <div className={`text-sm font-semibold ${
                                                speech_recognition.confidence > 0.8 ? 'text-green-300' :
                                                speech_recognition.confidence > 0.5 ? 'text-yellow-300' :
                                                'text-orange-300'
                                            }`}>
                                                {Math.round(speech_recognition.confidence * 100)}%
                                            </div>
                                        </div>
                                    )}
                                    
                                    {speech_recognition.language_detected && (
                                        <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400 mb-1">检测语言</div>
                                            <div className="text-sm font-semibold text-blue-300">
                                                {speech_recognition.language_detected === 'zh' ? '中文' :
                                                 speech_recognition.language_detected === 'en' ? '英文' : 
                                                 speech_recognition.language_detected}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {speech_recognition.segments_count !== undefined && (
                                        <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400 mb-1">音频段数</div>
                                            <div className="text-sm font-semibold text-purple-300">
                                                {speech_recognition.segments_count} 段
                                            </div>
                                        </div>
                                    )}
                                    
                                    {speech_recognition.word_count !== undefined && (
                                        <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400 mb-1">词汇总数</div>
                                            <div className="text-sm font-semibold text-indigo-300">
                                                {speech_recognition.word_count} 词
                                            </div>
                                        </div>
                                    )}
                                </div>
                                
                                {/* Additional metrics if available */}
                                {(speech_recognition.words_per_minute || speech_recognition.text_length) && (
                                    <div className="grid grid-cols-2 gap-4 mt-4">
                                        {speech_recognition.words_per_minute && (
                                            <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                                <div className="text-xs text-slate-400 mb-1">语速</div>
                                                <div className="text-sm font-semibold text-cyan-300">
                                                    {speech_recognition.words_per_minute} 词/分
                                                </div>
                                            </div>
                                        )}
                                        
                                        {speech_recognition.text_length && (
                                            <div className="bg-slate-800/50 p-3 rounded-lg text-center">
                                                <div className="text-xs text-slate-400 mb-1">文本长度</div>
                                                <div className="text-sm font-semibold text-emerald-300">
                                                    {speech_recognition.text_length} 字符
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Model Information */}
                                {speech_recognition.model_info && (
                                    <div className="bg-slate-800/50 p-3 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">模型信息</h5>
                                        <div className="text-xs text-slate-300">
                                            使用 Whisper {speech_recognition.model_info.model} 模型
                                            {speech_recognition.model_info.parameters && ` (${speech_recognition.model_info.parameters}参数)`}
                                            {speech_recognition.model_info.multilingual && " · 支持多语言"}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="bg-slate-800/50 p-4 rounded-lg">
                                <div className="text-slate-400 text-sm flex items-center gap-2 mb-2">
                                    <span>🔇</span>
                                    <span>此音频未检测到语音内容或语音识别失败</span>
                                </div>
                                {speech_recognition.error && (
                                    <div className="text-slate-500 text-xs">
                                        原因：{speech_recognition.error}
                                    </div>
                                )}
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