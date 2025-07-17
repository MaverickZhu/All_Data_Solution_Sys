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

                {/* Audio Preprocessing Information */}
                {speech_recognition?.preprocessing_info && (
                    <div className="bg-gradient-to-r from-purple-900/20 to-indigo-900/20 p-6 rounded-2xl border border-purple-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">🔧</span>
                            音频预处理与增强
                            {speech_recognition.preprocessing_info.enhancement_applied && (
                                <span className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded text-sm ml-2">
                                    ✨ 已增强
                                </span>
                            )}
                        </h4>
                        
                        <div className="space-y-4">
                            {/* Noise Analysis */}
                            {speech_recognition.preprocessing_info.noise_analysis && (
                                <div className="bg-black/30 p-4 rounded-lg">
                                    <h5 className="text-sm font-medium text-purple-400 mb-3">噪声分析</h5>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                        <div className="text-center">
                                            <div className="text-xs text-slate-400">信噪比</div>
                                            <div className={`text-sm font-semibold ${
                                                speech_recognition.preprocessing_info.noise_analysis.estimated_snr_db > 20 ? 'text-green-300' :
                                                speech_recognition.preprocessing_info.noise_analysis.estimated_snr_db > 10 ? 'text-yellow-300' :
                                                'text-red-300'
                                            }`}>
                                                {speech_recognition.preprocessing_info.noise_analysis.estimated_snr_db?.toFixed(1)} dB
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-xs text-slate-400">噪声水平</div>
                                            <div className={`text-sm font-semibold ${
                                                speech_recognition.preprocessing_info.noise_analysis.noise_level === 'low' ? 'text-green-300' :
                                                speech_recognition.preprocessing_info.noise_analysis.noise_level === 'medium' ? 'text-yellow-300' :
                                                'text-red-300'
                                            }`}>
                                                {speech_recognition.preprocessing_info.noise_analysis.noise_level === 'low' ? '低' :
                                                 speech_recognition.preprocessing_info.noise_analysis.noise_level === 'medium' ? '中' :
                                                 speech_recognition.preprocessing_info.noise_analysis.noise_level === 'high' ? '高' : '未知'}
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-xs text-slate-400">频谱平坦度</div>
                                            <div className="text-sm font-semibold text-blue-300">
                                                {speech_recognition.preprocessing_info.noise_analysis.spectral_flatness?.toFixed(3)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {/* Enhancement Status */}
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-purple-400 mb-3">增强处理状态</h5>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-slate-400">去噪处理</span>
                                        <span className={`text-sm ${speech_recognition.preprocessing_info.enhancement_applied ? 'text-green-300' : 'text-slate-400'}`}>
                                            {speech_recognition.preprocessing_info.enhancement_applied ? '✅ 已应用' : '⏭️ 已跳过'}
                                        </span>
                                    </div>
                                    {speech_recognition.preprocessing_info.preprocessing_error && (
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-slate-400">处理错误</span>
                                            <span className="text-sm text-red-300">⚠️ {speech_recognition.preprocessing_info.preprocessing_error}</span>
                                                                    </div>
                        )}

                        {/* 新增：智能文本优化结果展示 */}
                        {result.text_optimization && (
                            <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 p-6 rounded-lg border border-purple-500/30 shadow-lg">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-lg font-semibold text-purple-400 flex items-center gap-2">
                                        <span className="text-2xl">🧠</span>
                                        智能文本优化
                                    </h4>
                                    {result.text_optimization.success && (
                                        <span className="text-xs bg-purple-600/20 text-purple-300 px-3 py-1 rounded-full border border-purple-500/30">
                                            ✨ AI优化完成
                                        </span>
                                    )}
                                </div>

                                {result.text_optimization.success ? (
                                    <div className="space-y-4">
                                        {/* 优化后的文本 */}
                                        <div className="bg-black/30 p-4 rounded-lg border border-purple-500/20">
                                            <h5 className="text-sm font-medium text-purple-400 mb-2">优化后文本</h5>
                                            <div className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                                                {result.text_optimization.optimized_text}
                                            </div>
                                        </div>

                                        {/* 优化统计信息 */}
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                            <div className="bg-black/20 p-3 rounded-lg border border-purple-500/20 text-center">
                                                <div className="text-purple-300 font-medium">文本精简</div>
                                                <div className="text-xl font-bold text-purple-400">
                                                    {result.text_optimization.reduction_rate || 0}%
                                                </div>
                                            </div>
                                            <div className="bg-black/20 p-3 rounded-lg border border-purple-500/20 text-center">
                                                <div className="text-purple-300 font-medium">应用改进</div>
                                                <div className="text-xl font-bold text-purple-400">
                                                    {result.text_optimization.improvements?.length || 0}项
                                                </div>
                                            </div>
                                            <div className="bg-black/20 p-3 rounded-lg border border-purple-500/20 text-center">
                                                <div className="text-purple-300 font-medium">处理时间</div>
                                                <div className="text-xl font-bold text-purple-400">
                                                    {result.text_optimization.optimization_time || 0}ms
                                                </div>
                                            </div>
                                        </div>

                                        {/* 应用的改进措施 */}
                                        {result.text_optimization.improvements && result.text_optimization.improvements.length > 0 && (
                                            <div className="bg-black/20 p-4 rounded-lg border border-purple-500/20">
                                                <h5 className="text-sm font-medium text-purple-400 mb-2">应用的优化措施</h5>
                                                <div className="flex flex-wrap gap-2">
                                                    {result.text_optimization.improvements.map((improvement, index) => (
                                                        <span
                                                            key={index}
                                                            className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded-full text-xs border border-purple-500/30"
                                                        >
                                                            {improvement}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* 原始文本对比（可展开） */}
                                        <details className="bg-black/20 p-4 rounded-lg border border-purple-500/20">
                                            <summary className="text-sm font-medium text-purple-400 cursor-pointer">
                                                📋 查看原始识别文本对比
                                            </summary>
                                            <div className="mt-3 p-3 bg-black/30 rounded border border-gray-600">
                                                <div className="text-gray-400 text-xs mb-2">原始文本（{result.text_optimization.raw_text?.length || 0} 字符）：</div>
                                                <div className="text-gray-300 text-sm whitespace-pre-wrap opacity-75">
                                                    {result.text_optimization.raw_text}
                                                </div>
                                            </div>
                                        </details>
                                    </div>
                                ) : (
                                    <div className="text-center py-4">
                                        <div className="text-red-400 mb-2">❌ 文本优化失败</div>
                                        <div className="text-sm text-gray-400">
                                            {result.text_optimization.error || "未知错误"}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
                        </div>
                    </div>
                )}

                {/* Enhanced Speech Recognition Results */}
                {speech_recognition && (
                    <div className="bg-gradient-to-r from-green-900/20 to-teal-900/20 p-6 rounded-2xl border border-green-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">🎤</span>
                            智能语音识别结果
                            {speech_recognition.performance_metrics && speech_recognition.performance_metrics.device_used === 'cuda' && (
                                <span className="bg-green-500/20 text-green-300 px-2 py-1 rounded text-sm ml-2">
                                    🚀 GPU加速
                                </span>
                            )}
                            {speech_recognition.performance_metrics && speech_recognition.performance_metrics.transcription_time_seconds && (
                                <span className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded text-sm ml-2">
                                    ⚡ {speech_recognition.performance_metrics.transcription_time_seconds}s
                                </span>
                            )}
                        </h4>
                        
                        {speech_recognition.success ? (
                            <div className="space-y-6">
                                {/* Enhanced Transcribed Text */}
                                {speech_recognition.transcribed_text && (
                                    <div className="bg-black/30 p-5 rounded-lg border border-green-500/20">
                                        <div className="flex items-center justify-between mb-3">
                                            <h5 className="text-sm font-medium text-green-400">✨ 智能优化转录文本</h5>
                                            {speech_recognition.text_optimization?.success && (
                                                <span className="text-xs bg-green-600/20 text-green-300 px-2 py-1 rounded-full">
                                                    🧠 文本优化
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-slate-200 text-sm leading-relaxed border-l-2 border-green-500/30 pl-4">
                                            {speech_recognition.transcribed_text.split('\n\n').map((paragraph, pIndex) => (
                                                <div key={pIndex} className="mb-4 last:mb-0">
                                                    {paragraph.split('\n').map((sentence, sIndex) => (
                                                        <p key={sIndex} className="mb-1 last:mb-0">
                                                            {sentence.trim()}
                                                        </p>
                                                    ))}
                                                </div>
                                            ))}
                                        </div>
                                        
                                        {/* Text Optimization Information */}
                                        {speech_recognition.text_optimization?.success && speech_recognition.text_optimization.improvements && speech_recognition.text_optimization.improvements.length > 0 && (
                                            <div className="mt-4 p-3 bg-blue-900/20 rounded-lg border border-blue-500/20">
                                                <h6 className="text-xs font-medium text-blue-400 mb-2">应用的优化:</h6>
                                                <div className="flex flex-wrap gap-2">
                                                    {speech_recognition.text_optimization.improvements.map((improvement, index) => (
                                                        <span key={index} className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded-full">
                                                            {improvement}
                                                        </span>
                                                    ))}
                                                </div>
                                                
                                                {/* Optimization Statistics */}
                                                {speech_recognition.text_optimization.statistics && (
                                                    <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                                        <div className="bg-slate-800/30 p-2 rounded">
                                                            <div className="text-slate-400">句子数</div>
                                                            <div className="text-white font-medium">
                                                                {speech_recognition.text_optimization.statistics.sentence_count || 0}
                                                            </div>
                                                        </div>
                                                        <div className="bg-slate-800/30 p-2 rounded">
                                                            <div className="text-slate-400">段落数</div>
                                                            <div className="text-white font-medium">
                                                                {speech_recognition.text_optimization.statistics.paragraph_count || 0}
                                                            </div>
                                                        </div>
                                                        <div className="bg-slate-800/30 p-2 rounded">
                                                            <div className="text-slate-400">原始字数</div>
                                                            <div className="text-white font-medium">
                                                                {speech_recognition.text_optimization.statistics.original_word_count || 0}
                                                            </div>
                                                        </div>
                                                        <div className="bg-slate-800/30 p-2 rounded">
                                                            <div className="text-slate-400">优化字数</div>
                                                            <div className="text-white font-medium">
                                                                {speech_recognition.text_optimization.statistics.optimized_word_count || 0}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        
                                        {/* Show original text comparison if optimized */}
                                        {speech_recognition.raw_text && speech_recognition.raw_text !== speech_recognition.transcribed_text && (
                                            <details className="mt-4">
                                                <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-300">
                                                    查看原始识别文本
                                                </summary>
                                                <div className="mt-2 p-3 bg-slate-800/50 rounded text-xs text-slate-400 border-l-2 border-slate-600 pl-3">
                                                    <div className="leading-relaxed">
                                                        {speech_recognition.raw_text}
                                                    </div>
                                                </div>
                                            </details>
                                        )}
                                    </div>
                                )}
                                
                                {/* Enhanced Recognition Metrics */}
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
                                
                                {/* Confidence Distribution */}
                                {speech_recognition.confidence_distribution && (
                                    <div className="bg-black/20 p-4 rounded-lg mt-4">
                                        <h5 className="text-sm font-medium text-slate-300 mb-3">置信度分布</h5>
                                        <div className="grid grid-cols-3 gap-3">
                                            <div className="bg-green-600/20 p-3 rounded text-center">
                                                <div className="text-lg font-bold text-green-300">
                                                    {speech_recognition.confidence_distribution.high || 0}
                                                </div>
                                                <div className="text-xs text-green-400">高置信度段</div>
                                            </div>
                                            <div className="bg-yellow-600/20 p-3 rounded text-center">
                                                <div className="text-lg font-bold text-yellow-300">
                                                    {speech_recognition.confidence_distribution.medium || 0}
                                                </div>
                                                <div className="text-xs text-yellow-400">中等置信度段</div>
                                            </div>
                                            <div className="bg-orange-600/20 p-3 rounded text-center">
                                                <div className="text-lg font-bold text-orange-300">
                                                    {speech_recognition.confidence_distribution.low || 0}
                                                </div>
                                                <div className="text-xs text-orange-400">低置信度段</div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Enhancement Information */}
                                {speech_recognition.enhancement_info && speech_recognition.enhancement_info.enhancement_successful && (
                                    <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 p-4 rounded-lg border border-blue-500/20 mt-4">
                                        <h5 className="text-sm font-medium text-blue-400 mb-3 flex items-center gap-2">
                                            <span>🔧</span>
                                            文本增强详情
                                        </h5>
                                        
                                        {/* Enhancement Improvements */}
                                        {speech_recognition.enhancement_info.improvements && speech_recognition.enhancement_info.improvements.length > 0 && (
                                            <div className="mb-3">
                                                <div className="text-xs text-slate-400 mb-2">应用的改进:</div>
                                                <div className="flex flex-wrap gap-2">
                                                    {speech_recognition.enhancement_info.improvements.map((improvement, index) => (
                                                        <span key={index} className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded-full">
                                                            {improvement}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        
                                        {/* Quality Metrics */}
                                        {speech_recognition.enhancement_info.quality_metrics && (
                                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                                                <div className="bg-slate-800/30 p-2 rounded">
                                                    <div className="text-slate-400">质量分数</div>
                                                    <div className="text-white font-medium">
                                                        {Math.round(speech_recognition.enhancement_info.quality_metrics.overall_score * 100)}%
                                                    </div>
                                                </div>
                                                <div className="bg-slate-800/30 p-2 rounded">
                                                    <div className="text-slate-400">标点改进</div>
                                                    <div className="text-white font-medium">
                                                        +{speech_recognition.enhancement_info.quality_metrics.punctuation_improvement || 0}
                                                    </div>
                                                </div>
                                                <div className="bg-slate-800/30 p-2 rounded">
                                                    <div className="text-slate-400">句子数</div>
                                                    <div className="text-white font-medium">
                                                        {speech_recognition.enhancement_info.quality_metrics.sentence_count || 0}
                                                    </div>
                                                </div>
                                                <div className="bg-slate-800/30 p-2 rounded">
                                                    <div className="text-slate-400">重复率</div>
                                                    <div className="text-white font-medium">
                                                        {Math.round((speech_recognition.enhancement_info.quality_metrics.repetition_ratio || 0) * 100)}%
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                                
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