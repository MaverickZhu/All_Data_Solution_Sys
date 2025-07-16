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
    if (!result || result.analysis_type !== 'video') {
        return <div className="text-center text-slate-400 py-10">视频分析数据不可用或格式错误。</div>;
    }

    const { file_info, metadata, video_properties, quality_info, analysis_summary } = result;
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

    // 如果有缩略图，构建缩略图URL
    const thumbnailUrl = video_properties?.thumbnail_path ? 
        `${API_URL}/uploads/${video_properties.thumbnail_path.split('/uploads/')[1]}` : null;

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
                            {file_info?.format?.toUpperCase() || 'VIDEO'} 文件
                        </div>
                        <div className="text-sm text-slate-400 mt-2">
                            {quality_info?.file_size_mb} MB
                        </div>
                    </div>
                </div>

                {/* Basic Video Properties */}
                <div className="grid grid-cols-1 gap-4">
                    <StatCard 
                        label="分辨率" 
                        value={video_properties?.resolution} 
                        icon="📺"
                    />
                    <StatCard 
                        label="时长" 
                        value={analysis_summary?.duration_formatted} 
                        icon="⏱️"
                    />
                    <StatCard 
                        label="视频类型" 
                        value={analysis_summary?.video_type} 
                        icon="🎞️"
                    />
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
                            value={video_properties?.width ? `${video_properties.width} px` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="高度" 
                            value={video_properties?.height ? `${video_properties.height} px` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="帧率" 
                            value={video_properties?.fps ? `${video_properties.fps.toFixed(2)} FPS` : 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="总帧数" 
                            value={video_properties?.frame_count?.toLocaleString() || 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="宽高比" 
                            value={video_properties?.aspect_ratio || 'N/A'}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="时长(秒)" 
                            value={video_properties?.duration_seconds ? `${video_properties.duration_seconds.toFixed(2)}s` : 'N/A'}
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
                            value={quality_info?.resolution_category}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="帧率等级" 
                            value={quality_info?.frame_rate_category}
                            className="bg-black/30"
                        />
                        <StatCard 
                            label="文件大小" 
                            value={quality_info?.file_size_mb ? `${quality_info.file_size_mb} MB` : 'N/A'}
                            className="bg-black/30"
                        />
                    </div>
                </div>

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
                                这是一个 {analysis_summary?.format_info} 的{analysis_summary?.video_type}，
                                时长为 {analysis_summary?.duration_formatted}，
                                分辨率为 {video_properties?.resolution}，
                                文件大小为 {quality_info?.file_size_mb} MB。
                            </p>
                        </div>
                        
                        <div className="bg-black/30 p-4 rounded-lg">
                            <h5 className="text-sm font-medium text-sky-400 mb-2">质量分析</h5>
                            <p className="text-white">
                                视频质量为 {analysis_summary?.quality_summary}，
                                {quality_info?.resolution_category === '4K' && '支持超高清显示，'}
                                {quality_info?.resolution_category === 'Full HD' && '支持全高清显示，'}
                                {quality_info?.resolution_category === 'HD' && '支持高清显示，'}
                                帧率{quality_info?.frame_rate_category === '高帧率' ? '较高，播放流畅' : '标准，适合一般播放'}。
                            </p>
                        </div>

                        {video_properties?.frame_count && (
                            <div className="bg-black/30 p-4 rounded-lg">
                                <h5 className="text-sm font-medium text-sky-400 mb-2">技术参数</h5>
                                <p className="text-white">
                                    视频包含 {video_properties.frame_count.toLocaleString()} 帧，
                                    平均每秒 {video_properties.fps?.toFixed(2)} 帧，
                                    宽高比为 {video_properties.aspect_ratio}
                                    {video_properties.aspect_ratio > 1.7 ? '（宽屏格式）' : 
                                     video_properties.aspect_ratio > 1.2 ? '（标准宽屏）' : '（方形或竖屏格式）'}。
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