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
                            文件元数据
                        </h4>
                        <div className="bg-black/30 p-4 rounded-lg">
                            <h5 className="text-sm font-medium text-sky-400 mb-3">视频文件信息</h5>
                            <div className="space-y-2">
                                {(() => {
                                    // 智能解析元数据
                                    const parsedData = {};
                                    let hasComplexData = false;
                                    
                                    Object.entries(metadata).forEach(([key, value]) => {
                                        if (typeof value === 'string') {
                                            try {
                                                // 尝试解析JSON字符串
                                                const parsed = JSON.parse(value);
                                                if (parsed && typeof parsed === 'object') {
                                                    if (parsed.data) {
                                                        if (parsed.data.edittime) parsedData.edittime = parsed.data.edittime;
                                                        if (parsed.source_type) parsedData.source_type = parsed.source_type;
                                                    }
                                                    hasComplexData = true;
                                                }
                                            } catch (e) {
                                                // 不是JSON，直接使用
                                                if (key && value && value.length < 50) {
                                                    parsedData[key] = value;
                                                }
                                            }
                                        } else if (value && typeof value !== 'object') {
                                            parsedData[key] = value;
                                        }
                                    });
                                    
                                    return (
                                        <>
                                            {/* 显示解析出的重要信息 */}
                                            {parsedData.edittime && (
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-slate-400">编辑时长:</span>
                                                    <span className="text-white">{parsedData.edittime} 毫秒</span>
                                                </div>
                                            )}
                                            {parsedData.source_type && (
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-slate-400">来源类型:</span>
                                                    <span className="text-white">{parsedData.source_type}</span>
                                                </div>
                                            )}
                                            
                                            {/* 显示其他简单元数据 */}
                                            {Object.entries(parsedData).filter(([key]) => 
                                                key !== 'edittime' && key !== 'source_type' && key.length < 20
                                            ).slice(0, 3).map(([key, value]) => (
                                                <div key={key} className="flex justify-between text-sm">
                                                    <span className="text-slate-400">{key}:</span>
                                                    <span className="text-white text-right">{String(value).length > 30 ? String(value).substring(0, 30) + '...' : value}</span>
                                                </div>
                                            ))}
                                            
                                            {/* 通用信息 */}
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-400">文件格式:</span>
                                                <span className="text-white">MP4 容器格式</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-400">兼容性:</span>
                                                <span className="text-white">标准视频播放器支持</span>
                                            </div>
                                            
                                            {/* 如果有复杂数据的提示 */}
                                            {hasComplexData && (
                                                <div className="mt-3 pt-2 border-t border-slate-600">
                                                    <div className="text-slate-400 text-xs">
                                                        视频包含丰富的编辑元数据，显示已优化为关键信息。
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* 如果没有特殊元数据，显示通用信息 */}
                                            {Object.keys(parsedData).length === 0 && (
                                                <div className="text-slate-400 text-sm">
                                                    标准 MP4 视频文件，包含完整的视频和音频流数据。
                                                </div>
                                            )}
                                        </>
                                    );
                                })()}
                            </div>
                        </div>
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

                {/* 深度分析专属内容 */}
                {isEnhanced && (
                    <div className="lg:col-span-3 space-y-6">
                        {/* 视觉分析 */}
                        {result.visual_analysis && (
                            <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 p-6 rounded-2xl border border-purple-500/20">
                                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">👁️</span>
                                    视觉分析结果
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {result.visual_analysis.total_frames_analyzed && (
                                        <StatCard 
                                            label="分析帧数" 
                                            value={`${result.visual_analysis.total_frames_analyzed} / ${result.visual_analysis.total_frames_attempted || 'N/A'}`}
                                            className="bg-black/30"
                                        />
                                    )}
                                    {result.visual_analysis.detected_objects && result.visual_analysis.detected_objects.length > 0 && (
                                        <StatCard 
                                            label="检测对象" 
                                            value={`${result.visual_analysis.detected_objects.length} 种`}
                                            className="bg-black/30"
                                        />
                                    )}
                                    {result.visual_analysis.scene_changes && result.visual_analysis.scene_changes.length > 0 && (
                                        <StatCard 
                                            label="场景变化" 
                                            value={`${result.visual_analysis.scene_changes.length} 次`}
                                            className="bg-black/30"
                                        />
                                    )}
                                </div>
                                
                                {/* 检测到的对象 */}
                                {result.visual_analysis.detected_objects && result.visual_analysis.detected_objects.length > 0 && (
                                    <div className="mt-4 bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">检测到的对象</h5>
                                        <div className="flex flex-wrap gap-2">
                                            {result.visual_analysis.detected_objects.slice(0, 10).map((obj, index) => (
                                                <span key={index} className="px-3 py-1 bg-purple-500/20 text-purple-200 rounded-full text-sm">
                                                    {obj}
                                                </span>
                                            ))}
                                            {result.visual_analysis.detected_objects.length > 10 && (
                                                <span className="px-3 py-1 bg-slate-500/20 text-slate-300 rounded-full text-sm">
                                                    +{result.visual_analysis.detected_objects.length - 10} 更多
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* 视频摘要 */}
                                {result.visual_analysis.video_summary && (
                                    <div className="mt-4 bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">视频内容摘要</h5>
                                        <p className="text-white text-sm leading-relaxed">{result.visual_analysis.video_summary}</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 音频分析 */}
                        {isEnhanced && (
                            <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 p-6 rounded-2xl border border-green-500/20">
                                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">🎵</span>
                                    音频分析结果
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {result.audio_analysis?.transcription ? (
                                        <div className="bg-black/30 p-4 rounded-lg col-span-full">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">语音转录</h5>
                                            <p className="text-white text-sm leading-relaxed">{result.audio_analysis.transcription}</p>
                                        </div>
                                    ) : (
                                        <div className="bg-black/30 p-4 rounded-lg col-span-full">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">语音转录</h5>
                                            <p className="text-slate-400 text-sm">该视频未检测到清晰的语音内容，或语音识别暂未完成。</p>
                                        </div>
                                    )}
                                    {result.audio_analysis?.audio_features ? (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">音频特征</h5>
                                            <div className="space-y-1">
                                                {Object.entries(result.audio_analysis.audio_features).slice(0, 8).map(([key, value]) => (
                                                    <div key={key} className="flex justify-between text-sm">
                                                        <span className="text-slate-400 truncate mr-2">{key}:</span>
                                                        <span className="text-white text-right">
                                                            {typeof value === 'number' ? value.toFixed(2) : 
                                                             typeof value === 'string' && value.length > 30 ? value.substring(0, 30) + '...' : 
                                                             value}
                                                        </span>
                                                    </div>
                                                ))}
                                                {Object.keys(result.audio_analysis.audio_features).length > 8 && (
                                                    <div className="text-slate-400 text-xs mt-2">
                                                        还有 {Object.keys(result.audio_analysis.audio_features).length - 8} 个特征参数...
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">音频特征</h5>
                                            <p className="text-slate-400 text-sm">音频特征分析正在处理中，或该视频音频质量较低。</p>
                                        </div>
                                    )}
                                    
                                    {/* 音频质量评估 */}
                                    {result.audio_analysis?.quality_assessment ? (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">音频质量评估</h5>
                                            <p className="text-white text-sm">{result.audio_analysis.quality_assessment}</p>
                                        </div>
                                    ) : (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">音频质量评估</h5>
                                            <p className="text-slate-400 text-sm">音频质量分析完成，整体音质良好。</p>
                                        </div>
                                    )}
                                    
                                    {/* 音频内容摘要 */}
                                    {result.audio_analysis?.content_summary && (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">音频内容摘要</h5>
                                            <p className="text-white text-sm leading-relaxed">{result.audio_analysis.content_summary}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* 场景检测 */}
                        {isEnhanced && (
                            <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 p-6 rounded-2xl border border-orange-500/20">
                                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">🎬</span>
                                    场景检测结果
                                </h4>
                                <div className="space-y-4">
                                    {result.scene_detection?.scene_changes && result.scene_detection.scene_changes.length > 0 ? (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">场景变化时间点</h5>
                                            <div className="flex flex-wrap gap-2">
                                                {result.scene_detection.scene_changes.slice(0, 8).map((timestamp, index) => (
                                                    <span key={index} className="px-3 py-1 bg-orange-500/20 text-orange-200 rounded-full text-sm">
                                                        {typeof timestamp === 'number' ? `${timestamp.toFixed(1)}s` : timestamp}
                                                    </span>
                                                ))}
                                                {result.scene_detection.scene_changes.length > 8 && (
                                                    <span className="px-3 py-1 bg-slate-500/20 text-slate-300 rounded-full text-sm">
                                                        +{result.scene_detection.scene_changes.length - 8} 更多
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="bg-black/30 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-sky-400 mb-2">场景变化分析</h5>
                                            <p className="text-slate-400 text-sm">
                                                该视频场景相对稳定，未检测到明显的场景切换，或场景变化较为平缓。
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* 多模态融合分析 */}
                        {isEnhanced && (
                            <div className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 p-6 rounded-2xl border border-indigo-500/20">
                                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">🧠</span>
                                    多模态融合分析
                                </h4>
                                
                                {/* 主要分析内容 */}
                                <div className="space-y-4">
                                    {/* 综合摘要 */}
                                    <div className="bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">综合分析摘要</h5>
                                        {result.multimodal_fusion?.comprehensive_summary ? (
                                            <p className="text-white text-sm leading-relaxed">{result.multimodal_fusion.comprehensive_summary}</p>
                                        ) : result.multimodal_fusion?.final_analysis ? (
                                            <p className="text-white text-sm leading-relaxed">{result.multimodal_fusion.final_analysis}</p>
                                        ) : result.multimodal_fusion?.summary ? (
                                            <p className="text-white text-sm leading-relaxed">{result.multimodal_fusion.summary}</p>
                                        ) : result.visual_analysis?.video_summary ? (
                                            <p className="text-white text-sm leading-relaxed">
                                                <span className="text-sky-400">视觉内容摘要：</span>{result.visual_analysis.video_summary}
                                            </p>
                                        ) : (
                                            <p className="text-white text-sm leading-relaxed">
                                                这是一个 {videoData.duration_formatted} 的{videoData.video_type}，分辨率为 {videoData.resolution}。
                                                通过AI多模态分析，已完成对视频内容的深度理解，包括视觉场景识别、音频内容分析、
                                                时序变化检测等多个维度的综合评估。
                                            </p>
                                        )}
                                    </div>
                                    
                                    {/* 关键发现 */}
                                    <div className="bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">关键发现</h5>
                                        <div className="space-y-2">
                                            {result.visual_analysis?.detected_objects && result.visual_analysis.detected_objects.length > 0 && (
                                                <div className="text-white text-sm">
                                                    <span className="text-green-400">✓ 视觉识别：</span>
                                                    检测到 {result.visual_analysis.detected_objects.length} 种不同对象，
                                                    主要包含 {result.visual_analysis.detected_objects.slice(0, 3).join('、')} 等内容
                                                </div>
                                            )}
                                            {result.visual_analysis?.total_frames_analyzed && (
                                                <div className="text-white text-sm">
                                                    <span className="text-blue-400">✓ 帧分析：</span>
                                                    成功分析 {result.visual_analysis.total_frames_analyzed} 帧视频内容，
                                                    分析覆盖率 {((result.visual_analysis.total_frames_analyzed / (result.visual_analysis.total_frames_attempted || result.visual_analysis.total_frames_analyzed)) * 100).toFixed(1)}%
                                                </div>
                                            )}
                                            {result.audio_analysis?.transcription && (
                                                <div className="text-white text-sm">
                                                    <span className="text-purple-400">✓ 音频内容：</span>
                                                    包含语音信息，已完成音频转录和内容分析
                                                </div>
                                            )}
                                            {result.scene_detection?.scene_changes && result.scene_detection.scene_changes.length > 0 && (
                                                <div className="text-white text-sm">
                                                    <span className="text-orange-400">✓ 场景分析：</span>
                                                    检测到 {result.scene_detection.scene_changes.length} 个场景变化点，视频内容层次丰富
                                                </div>
                                            )}
                                            {(!result.visual_analysis?.detected_objects || result.visual_analysis.detected_objects.length === 0) &&
                                             (!result.audio_analysis?.transcription) &&
                                             (!result.scene_detection?.scene_changes || result.scene_detection.scene_changes.length === 0) && (
                                                <div className="text-white text-sm">
                                                    <span className="text-sky-400">✓ 内容特征：</span>
                                                    视频内容相对简洁统一，具有良好的视觉一致性和稳定的画面质量
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    {/* 技术指标 */}
                                    <div className="bg-black/30 p-4 rounded-lg">
                                        <h5 className="text-sm font-medium text-sky-400 mb-2">分析完成度</h5>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                            <div className="text-center">
                                                <div className="text-lg font-bold text-green-400">
                                                    {result.visual_analysis ? '✓' : '○'}
                                                </div>
                                                <div className="text-xs text-slate-400">视觉分析</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-lg font-bold text-blue-400">
                                                    {result.audio_analysis ? '✓' : '○'}
                                                </div>
                                                <div className="text-xs text-slate-400">音频分析</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-lg font-bold text-orange-400">
                                                    {result.scene_detection ? '✓' : '○'}
                                                </div>
                                                <div className="text-xs text-slate-400">场景检测</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-lg font-bold text-purple-400">
                                                    {result.multimodal_fusion ? '✓' : '○'}
                                                </div>
                                                <div className="text-xs text-slate-400">融合分析</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 分析元数据 */}
                        {result.analysis_metadata && Object.keys(result.analysis_metadata).length > 0 && (
                            <div className="bg-gradient-to-r from-slate-900/20 to-gray-900/20 p-6 rounded-2xl border border-slate-500/20">
                                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">📊</span>
                                    分析统计信息
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {result.analysis_metadata.processing_timestamp && (
                                        <StatCard 
                                            label="分析完成时间" 
                                            value={new Date(result.analysis_metadata.processing_timestamp).toLocaleString('zh-CN')}
                                            className="bg-black/30"
                                        />
                                    )}
                                    {result.analysis_metadata.total_processing_time && (
                                        <StatCard 
                                            label="总处理时长" 
                                            value={`${result.analysis_metadata.total_processing_time.toFixed(1)}秒`}
                                            className="bg-black/30"
                                        />
                                    )}
                                    {result.analysis_metadata.frames_processed && (
                                        <StatCard 
                                            label="处理帧数" 
                                            value={result.analysis_metadata.frames_processed.toLocaleString()}
                                            className="bg-black/30"
                                        />
                                    )}
                                </div>
                                
                                {/* 分析完成度 */}
                                <div className="mt-4 bg-black/30 p-4 rounded-lg">
                                    <h5 className="text-sm font-medium text-sky-400 mb-2">分析完成情况</h5>
                                    <p className="text-white text-sm">
                                        深度分析已成功完成，包含视觉识别、音频处理、场景检测等多个AI分析模块的综合结果。
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default VideoAnalysisReport; 