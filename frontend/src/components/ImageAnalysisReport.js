import React, { useState } from 'react';

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

const ColorSwatch = ({ color }) => {
    // 处理十六进制颜色字符串（如 "#ff0000"）
    const hexColor = typeof color === 'string' ? color : `rgb(${color.join(',')})`;
    return (
        <div className="flex items-center gap-3 bg-slate-800/50 p-2 rounded-lg">
            <div 
                className="w-8 h-8 rounded-md border-2 border-white/20" 
                style={{ backgroundColor: hexColor }}
            ></div>
            <span className="font-mono text-sm text-slate-300">{hexColor}</span>
        </div>
    );
};

const ImageAnalysisReport = ({ result, filePath }) => {
    const [showExif, setShowExif] = useState(false);

    if (!result || !result.image_properties) {
        return <div className="text-center text-slate-400 py-10">图像分析数据不可用或格式错误。</div>;
    }

    const { dimensions, file_size_bytes, dominant_colors, exif_data } = result.image_properties;
    const imageUrl = `${API_URL}/uploads/${filePath}`;
    const hasExif = exif_data && Object.keys(exif_data).length > 0;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 text-slate-200">
            {/* Left Column: Image Preview and Basic Info */}
            <div className="lg:col-span-1 space-y-6">
                <div className="bg-black/20 p-4 rounded-2xl border border-white/10">
                    <img 
                        src={imageUrl} 
                        alt="Analyzed" 
                        className="rounded-lg object-contain w-full max-h-96"
                        onError={(e) => { e.target.onerror = null; e.target.src = 'https://placehold.co/600x400/1a202c/94a3b8?text=Image+Not+Found'; }}
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <StatCard label="宽度" value={dimensions ? `${dimensions.width} px` : 'N/A'} />
                    <StatCard label="高度" value={dimensions ? `${dimensions.height} px` : 'N/A'} />
                    <StatCard label="文件大小" value={file_size_bytes ? `${(file_size_bytes / 1024).toFixed(2)} KB` : 'N/A'} />
                </div>
            </div>

            {/* Right Column: Analysis Details */}
            <div className="lg:col-span-2 space-y-6">
                {/* Dominant Colors */}
                {dominant_colors && dominant_colors.length > 0 && (
                    <div className="bg-black/20 p-6 rounded-2xl border border-white/10">
                        <h4 className="text-lg font-semibold text-white mb-4">主色调</h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {dominant_colors.map((color, index) => (
                                <ColorSwatch key={index} color={color} />
                            ))}
                        </div>
                    </div>
                )}

                {/* EXIF Data */}
                {hasExif && (
                    <div className="bg-black/20 p-6 rounded-2xl border border-white/10">
                        <button 
                            onClick={() => setShowExif(!showExif)}
                            className="w-full flex justify-between items-center text-lg font-semibold text-white mb-4"
                        >
                            <span>EXIF 元数据</span>
                            <span className={`transform transition-transform ${showExif ? 'rotate-180' : ''}`}>▼</span>
                        </button>
                        {showExif && (
                            <div className="overflow-x-auto max-h-96">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-800/50 text-xs text-slate-400 uppercase">
                                        <tr>
                                            <th className="px-4 py-2 rounded-l-lg">标签</th>
                                            <th className="px-4 py-2 rounded-r-lg">值</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-slate-900/50">
                                        {Object.entries(exif_data).map(([key, value]) => (
                                            <tr key={key} className="border-b border-slate-700/50 last:border-b-0">
                                                <td className="px-4 py-2 font-medium text-slate-300 whitespace-nowrap">{key}</td>
                                                <td className="px-4 py-2 text-white whitespace-pre-wrap break-all">{String(value)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ImageAnalysisReport; 