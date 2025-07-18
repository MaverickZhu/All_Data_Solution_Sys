import React from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8088';

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

const VideoAnalysisReport = ({ result, filePath }) => {
    if (!result || (result.analysis_type !== 'video' && result.analysis_type !== 'video_enhanced')) {
        return <div className="text-center text-slate-400 py-10">视频分析数据不可用或格式错误。</div>;
    }

    // 支持增强分析和基础分析
    const isEnhanced = result.analysis_type === 'video_enhanced';
    const { 
        file_info, 
        metadata, 
        video_properties, 
        quality_info, 
        analysis_summary, 
        enhanced_metadata, 
        primary_thumbnail, 
        thumbnails,
        format,
        file_size
    } = result;
    
    const hasError = result.error;

    if (hasError) {
        return (
            <div className="text-center text-red-400 py-10">
                <div className="text-6xl mb-4">⚠️</div>
                <div>视频分析失败</div>
                <div className="text-sm text-slate-400 mt-2">{result.error}</div>
            </div>
        );
    }

    // 构建缩略图URL（支持增强分析和基础分析）
    const getThumbnailUrl = (path) => {
        if (!path) return null;
        const pathParts = path.split('/uploads/');
        return pathParts.length > 1 ? `${API_URL}/uploads/${pathParts[1]}` : null;
    };
    
    const thumbnailUrl = isEnhanced ? 
        getThumbnailUrl(primary_thumbnail) : 
        getThumbnailUrl(video_properties?.thumbnail_path);

    // 统一的数据获取函数
    const getVideoData = () => {
        if (isEnhanced) {
            return {
                width: enhanced_metadata?.width || 'N/A',
                height: enhanced_metadata?.height || 'N/A',
                fps: enhanced_metadata?.fps || 'N/A',
                duration: enhanced_metadata?.duration || 0,
                duration_formatted: enhanced_metadata?.duration ? 
                    `${Math.floor(enhanced_metadata.duration / 60)}分${Math.floor(enhanced_metadata.duration % 60)}秒` : 'N/A',
                resolution: enhanced_metadata?.width && enhanced_metadata?.height ? 
                    `${enhanced_metadata.width}x${enhanced_metadata.height}` : 'N/A',
                aspect_ratio: enhanced_metadata?.width && enhanced_metadata?.height ? 
                    (enhanced_metadata.width / enhanced_metadata.height).toFixed(2) : 'N/A',
                frame_count: enhanced_metadata?.nb_frames || enhanced_metadata?.frame_count || 'N/A',
                file_size_mb: file_size ? Math.round(file_size / (1024 * 1024)) : 'N/A',
                format_name: format || enhanced_metadata?.format_name || file_info?.format || 'N/A',
                video_type: enhanced_metadata?.duration < 30 ? "短视频" : 
                           enhanced_metadata?.duration < 300 ? "中等时长视频" : 
                           enhanced_metadata?.duration < 3600 ? "长视频" : "超长视频",
                resolution_category: enhanced_metadata?.width >= 3840 ? '4K' : 
                                   enhanced_metadata?.width >= 1920 ? 'Full HD' : 
                                   enhanced_metadata?.width >= 1280 ? 'HD' : '标清',
                frame_rate_category: enhanced_metadata?.fps >= 60 ? '高帧率' : 
                                   enhanced_metadata?.fps >= 30 ? '标准帧率' : '低帧率'
            };
        } else {
            return {
                width: video_properties?.width || 'N/A',
                height: video_properties?.height || 'N/A',
                fps: video_properties?.fps || 'N/A',
                duration: video_properties?.duration_seconds || 0,
                duration_formatted: analysis_summary?.duration_formatted || 'N/A',
                resolution: video_properties?.resolution || 'N/A',
                aspect_ratio: video_properties?.aspect_ratio || 'N/A',
                frame_count: video_properties?.frame_count || 'N/A',
                file_size_mb: quality_info?.file_size_mb || 'N/A',
                format_name: file_info?.format || 'N/A',
                video_type: analysis_summary?.video_type || 'N/A',
                resolution_category: quality_info?.resolution_category || 'N/A',
                frame_rate_category: quality_info?.frame_rate_category || 'N/A'
            };
        }
    };

    const videoData = getVideoData();

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 text-slate-200">
            {/* Left Column: Video Preview and Basic Info */}
            <div className="lg:col-span-1 space-y-6">
                {/* Video Thumbnail or Icon */}
                <div className="bg-black/20 p-4 rounded-2xl border border-white/10">
                    {thumbnailUrl ? (
                        <img 
                            src={thumbnailUrl} 
                            alt="Video Thumbnail" 
                            className="rounded-lg object-cover w-full max-h-64"
                            onError={(e) => { 
                                e.target.onerror = null; 
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                            }}
                        />
                    ) : null}
                    <div className="flex flex-col items-center justify-center py-12" 
                         style={{display: thumbnailUrl ? 'none' : 'flex'}}>
                        <div className="text-8xl mb-4">🎬</div>
                        <div className="text-lg font-semibold text-white">
                            {videoData.format_name.toUpperCase()} 文件
                        </div>
                        <div className="text-sm text-slate-400 mt-2">
                            {videoData.file_size_mb !== 'N/A' ? `${videoData.file_size_mb} MB` : 'N/A'}
                        </div>
                    </div>
                    
                    {/* 多缩略图显示 */}
                    {isEnhanced && thumbnails && thumbnails.length > 1 && (
                        <div className="mt-4">
                            <div className="text-sm text-slate-400 mb-2">更多预览</div>
                            <div className="grid grid-cols-3 gap-2">
                                {thumbnails.slice(0, 3).map((thumb, index) => (
                                    <img 
                                        key={index}
                                        src={getThumbnailUrl(thumb)} 
                                        alt={`缩略图 ${index + 1}`}
                                        className="rounded object-cover w-full h-16"
                                        onError={(e) => { e.target.style.display = 'none'; }}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Basic Video Properties */}
                <div className="grid grid-cols-1 gap-4">
                    <StatCard 
                        label="分辨率" 
                        value={videoData.resolution} 
                        icon="📺"
                    />
                    <StatCard 
                        label="时长" 
                        value={videoData.duration_formatted} 
                        icon="⏱️"
                    />
                    <StatCard 
                        label="视频类型" 
                        value={videoData.video_type} 
                        icon="🎞️"
                    />
                    {isEnhanced && enhanced_metadata?.has_audio && (
                        <StatCard 
                            label="音频" 
                            value={enhanced_metadata?.audio_codec ? `${enhanced_metadata.audio_codec.toUpperCase()}` : "有音频"} 
                            icon="🔊"
                        />
                    )}
                </div>
            </div>

            {/* Right Column: Detailed Analysis */}
            <div className="lg:col-span-2 space-y-6">
                {/* Video Properties */}
                <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 p-6 rounded-2xl border border-purple-500/20">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="text-2xl">🎥</span>
                        视频属性
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <StatCard 
                            label="宽度" 
                            value={videoData.width !== 'N/A' ? `${videoData.width} px` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="高度" 
                            value={videoData.height !== 'N/A' ? `${videoData.height} px` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="帧率" 
                            value={videoData.fps !== 'N/A' ? `${parseFloat(videoData.fps).toFixed(2)} FPS` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="总帧数" 
                            value={videoData.frame_count !== 'N/A' ? videoData.frame_count.toLocaleString() : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="宽高比" 
                            value={videoData.aspect_ratio}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="时长(秒)" 
                            value={videoData.duration ? `${videoData.duration.toFixed(2)}s` : 'N/A'}
                            className="bg-black/30"
                        />
                    </div>
                </div>

                {/* Quality Information */}
                <div className="bg-gradient-to-r from-green-900/20 to-teal-900/20 p-6 rounded-2xl border border-green-500/20">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="text-2xl">⭐</span>
                        质量信息
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <StatCard 
                            label="分辨率等级" 
                            value={videoData.resolution_category}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="帧率等级" 
                            value={videoData.frame_rate_category}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="文件大小" 
                            value={videoData.file_size_mb !== 'N/A' ? `${videoData.file_size_mb} MB` : 'N/A'}
                            className="bg-black/30"
                        />
                    </div>
                </div>

                {/* Enhanced Metadata */}
                {isEnhanced && enhanced_metadata && (
                    <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 p-6 rounded-2xl border border-orange-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">📋</span>
                            增强元数据
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <StatCard 
                                label="格式名称" 
                                value={enhanced_metadata.format_name || format || 'N/A'}
                                className="bg-black/30"
                            />
                            <StatCard 
                                label="比特率" 
                                value={enhanced_metadata.bit_rate ? `${Math.round(enhanced_metadata.bit_rate / 1000)} kbps` : 'N/A'}
                                className="bg-black/30"
                            />
                            <StatCard 
                                label="流数量" 
                                value={enhanced_metadata.nb_streams || 'N/A'}
                                className="bg-black/30"
                            />
                            <StatCard 
                                label="视频编码" 
                                value={enhanced_metadata.video_codec?.toUpperCase() || 'N/A'}
                                className="bg-black/30"
                            />
                            <StatCard 
                                label="音频编码" 
                                value={enhanced_metadata.audio_codec?.toUpperCase() || 'N/A'}
                                className="bg-black/30"
                            />
                            <StatCard 
                                label="像素格式" 
                                value={enhanced_metadata.pixel_format || 'N/A'}
                                className="bg-black/30"
                            />
                        </div>
                    </div>
                )}

                {/* Metadata */}
                {metadata && Object.keys(metadata).length > 0 && (
                    <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 p-6 rounded-2xl border border-orange-500/20">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="text-2xl">📋</span>
                            元数据信息
                        </h4>
                        <MetadataCard title="视频元数据" data={metadata} />
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
                                这是一个 {videoData.format_name.toUpperCase()} 格式的{videoData.video_type}，
                                时长为 {videoData.duration_formatted}，
                                分辨率为 {videoData.resolution}，
                                文件大小为 {videoData.file_size_mb !== 'N/A' ? `${videoData.file_size_mb} MB` : 'N/A'}。
                            </p>
                        </div>
                        
                        <div className="bg-black/30 p-4 rounded-lg">
                            <h5 className="text-sm font-medium text-sky-400 mb-2">质量分析</h5>
                            <p className="text-white">
                                {isEnhanced ? (
                                    result.content_analysis ? 
                                        `视频${result.content_analysis.brightness_analysis?.category || '亮度正常'}，${result.content_analysis.contrast_analysis?.category || '对比度正常'}，画面${result.content_analysis.visual_stability?.brightness_stability || '稳定'}。` :
                                        `视频编码格式为 ${enhanced_metadata?.video_codec?.toUpperCase() || '未知'}，${enhanced_metadata?.has_audio ? '包含音频轨道' : '无音频'}。`
                                ) : (
                                    `视频质量为 ${analysis_summary?.quality_summary || '良好'}，
                                    ${videoData.resolution_category === '4K' && '支持超高清显示，'}
                                    ${videoData.resolution_category === 'Full HD' && '支持全高清显示，'}
                                    ${videoData.resolution_category === 'HD' && '支持高清显示，'}
                                    帧率${videoData.frame_rate_category === '高帧率' ? '较高，播放流畅' : '标准，适合一般播放'}。`
                                )}
                            </p>
                        </div>

                        {/* 增强分析专有：内容分析 */}
                        {isEnhanced && result.content_analysis && (
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-sky-400 mb-2">内容分析</h5>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">平均亮度:</span>
                                        <span className="text-white">{result.content_analysis.brightness_analysis?.average} ({result.content_analysis.brightness_analysis?.category})</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">平均对比度:</span>
                                        <span className="text-white">{result.content_analysis.contrast_analysis?.average} ({result.content_analysis.contrast_analysis?.category})</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">画面稳定性:</span>
                                        <span className="text-white">{result.content_analysis.visual_stability?.brightness_stability}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">分析帧数:</span>
                                        <span className="text-white">{result.content_analysis.analyzed_frames} 帧</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {/* 增强分析专有：编码信息 */}
                        {isEnhanced && enhanced_metadata && (
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-sky-400 mb-2">编码信息</h5>
                                <div className="space-y-2">
                                    {enhanced_metadata.video_codec && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">视频编码:</span>
                                            <span className="text-white">{enhanced_metadata.video_codec.toUpperCase()}</span>
                                        </div>
                                    )}
                                    {enhanced_metadata.audio_codec && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">音频编码:</span>
                                            <span className="text-white">{enhanced_metadata.audio_codec.toUpperCase()}</span>
                                        </div>
                                    )}
                                    {enhanced_metadata.bit_rate > 0 && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">比特率:</span>
                                            <span className="text-white">{Math.round(enhanced_metadata.bit_rate / 1000)} kbps</span>
                                        </div>
                                    )}
                                    {enhanced_metadata.pixel_format && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">像素格式:</span>
                                            <span className="text-white">{enhanced_metadata.pixel_format}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {videoData.frame_count !== 'N/A' && (
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-sky-400 mb-2">技术参数</h5>
                                <p className="text-white">
                                    {videoData.frame_count !== 'N/A' && `视频包含 ${videoData.frame_count.toLocaleString()} 帧，`}
                                    {videoData.fps !== 'N/A' && `平均每秒 ${parseFloat(videoData.fps).toFixed(2)} 帧，`}
                                    {videoData.aspect_ratio !== 'N/A' && `宽高比为 ${videoData.aspect_ratio}`}
                                    {videoData.aspect_ratio !== 'N/A' && (
                                        videoData.aspect_ratio > 1.7 ? '（宽屏格式）' : 
                                        videoData.aspect_ratio > 1.2 ? '（标准宽屏）' : '（方形或竖屏格式）'
                                    )}。
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoAnalysisReport; 