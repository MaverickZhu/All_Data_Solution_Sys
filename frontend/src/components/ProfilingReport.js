import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import EChartsVisualization from './EChartsVisualization';
import ImageAnalysisReport from './ImageAnalysisReport';


const StatCard = ({ label, value, icon, className = '' }) => (
    <div className={`bg-slate-800/50 p-4 rounded-lg flex items-center gap-4 ${className}`}>
        {icon && <div className="text-sky-400 text-2xl">{icon}</div>}
        <div>
            <div className="text-sm text-slate-400">{label}</div>
            <div className="text-xl font-bold text-white">{value}</div>
        </div>
    </div>
);

const Section = ({ title, children, icon }) => (
    <div className="rounded-2xl bg-black/20 backdrop-blur-md border border-white/10 shadow-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
            {icon}
            {title}
        </h3>
        <div className="border-t border-white/10 pt-4">
            {children}
        </div>
    </div>
);

const InteractiveColumnAnalysis = ({ columnAnalysis }) => {
    const [selectedColumn, setSelectedColumn] = useState(null);
    const [chartType, setChartType] = useState('histogram');
    const [showColumnSelector, setShowColumnSelector] = useState(false);

    // 检查columnAnalysis是否有效
    if (!columnAnalysis || Object.keys(columnAnalysis).length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-slate-400">暂无列分析数据</div>
            </div>
        );
    }

    // 获取重要的列（数值列、高基数列、有缺失值的列）
    const getImportantColumns = () => {
        const columns = Object.entries(columnAnalysis);
        
        // 数值列
        const numericColumns = columns.filter(([_, col]) => 
            col.dtype?.includes('int') || col.dtype?.includes('float')
        );
        
        // 高基数列（可能是ID或唯一标识）
        const highCardinalityColumns = columns.filter(([_, col]) => 
            col.unique_percentage > 80 && col.unique_count > 10
        );
        
        // 有缺失值的列
        const missingValueColumns = columns.filter(([_, col]) => 
            col.null_count > 0
        );
        
        // 文本列（取前几个最常见的）
        const textColumns = columns.filter(([_, col]) => 
            col.dtype === 'object' && col.most_common
        ).slice(0, 3);

        return {
            numeric: numericColumns,
            highCardinality: highCardinalityColumns,
            withMissing: missingValueColumns,
            text: textColumns
        };
    };

    const importantColumns = getImportantColumns();
    const allColumns = Object.entries(columnAnalysis);

    // 默认选择第一个数值列，如果没有则选择第一列
    const defaultColumn = importantColumns.numeric[0] || allColumns[0];
    const currentColumn = selectedColumn || defaultColumn;

    const renderColumnCard = (columnName, columnData) => {
        const isNumeric = columnData.dtype?.includes('int') || columnData.dtype?.includes('float');
        const hasStats = columnData.mean !== undefined;
        
        return (
            <div 
                key={columnName}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    currentColumn && currentColumn[0] === columnName 
                        ? 'bg-sky-900/50 border-sky-500/50' 
                        : 'bg-slate-800/30 border-slate-700/50 hover:bg-slate-700/30'
                }`}
                onClick={() => setSelectedColumn([columnName, columnData])}
            >
                <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-white truncate">{columnName}</h4>
                    <span className={`text-xs px-2 py-1 rounded ${
                        isNumeric ? 'bg-blue-500/20 text-blue-300' : 'bg-green-500/20 text-green-300'
                    }`}>
                        {columnData.dtype}
                    </span>
                </div>
                
                <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                        <span className="text-slate-400">非空值:</span>
                        <span className="text-white">{columnData.non_null_count}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-400">唯一值:</span>
                        <span className="text-white">{columnData.unique_count}</span>
                    </div>
                    {columnData.null_count > 0 && (
                        <div className="flex justify-between">
                            <span className="text-slate-400">缺失值:</span>
                            <span className="text-red-400">{columnData.null_count}</span>
                        </div>
                    )}
                    {hasStats && (
                        <div className="flex justify-between">
                            <span className="text-slate-400">均值:</span>
                            <span className="text-white">{columnData.mean}</span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const renderVisualization = () => {
        if (!currentColumn) return null;
        
        const [columnName, columnData] = currentColumn;
        const isNumeric = columnData.dtype?.includes('int') || columnData.dtype?.includes('float');
        
        return (
            <div className="bg-slate-800/30 p-6 rounded-lg border border-slate-700/50">
                <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold text-white">
                        {columnName} - {chartType === 'histogram' ? '分布图' : 
                         chartType === 'pie' ? '饼图' : '箱线图'}
                    </h4>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setChartType('histogram')}
                            className={`px-3 py-1 rounded text-sm ${
                                chartType === 'histogram' 
                                    ? 'bg-sky-600 text-white' 
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                            }`}
                        >
                            分布图
                        </button>
                        {!isNumeric && (
                            <button
                                onClick={() => setChartType('pie')}
                                className={`px-3 py-1 rounded text-sm ${
                                    chartType === 'pie' 
                                        ? 'bg-sky-600 text-white' 
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                            >
                                饼图
                            </button>
                        )}
                        {isNumeric && (
                            <button
                                onClick={() => setChartType('box')}
                                className={`px-3 py-1 rounded text-sm ${
                                    chartType === 'box' 
                                        ? 'bg-sky-600 text-white' 
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                            >
                                箱线图
                            </button>
                        )}
                    </div>
                </div>
                
                {/* 使用新的ECharts组件 */}
                <EChartsVisualization
                    columnName={columnName}
                    columnData={columnData}
                    chartType={chartType}
                />
                
                {/* 统计信息 */}
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard label="数据类型" value={columnData.dtype} />
                    <StatCard label="唯一值" value={columnData.unique_count} />
                    <StatCard label="缺失率" value={`${((columnData.null_count / (columnData.non_null_count + columnData.null_count)) * 100).toFixed(1)}%`} />
                    {isNumeric && columnData.mean && (
                        <StatCard label="均值" value={columnData.mean} />
                    )}
                    {!isNumeric && columnData.avg_length && (
                        <StatCard label="平均长度" value={columnData.avg_length} />
                    )}
                </div>
                
                {/* 详细统计 */}
                {isNumeric && (
                    <div className="mt-4 bg-slate-900/50 p-4 rounded-lg">
                        <h5 className="font-semibold text-white mb-2">数值统计</h5>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                            <div>
                                <span className="text-slate-400">最小值:</span>
                                <div className="text-white font-mono">{columnData.min}</div>
                            </div>
                            <div>
                                <span className="text-slate-400">Q1:</span>
                                <div className="text-white font-mono">{columnData.quartiles?.q25}</div>
                            </div>
                            <div>
                                <span className="text-slate-400">中位数:</span>
                                <div className="text-white font-mono">{columnData.median}</div>
                            </div>
                            <div>
                                <span className="text-slate-400">Q3:</span>
                                <div className="text-white font-mono">{columnData.quartiles?.q75}</div>
                            </div>
                            <div>
                                <span className="text-slate-400">最大值:</span>
                                <div className="text-white font-mono">{columnData.max}</div>
                            </div>
                        </div>
                    </div>
                )}
                
                {!isNumeric && columnData.most_common && (
                    <div className="mt-4 bg-slate-900/50 p-4 rounded-lg">
                        <h5 className="font-semibold text-white mb-2">最常见值</h5>
                        <div className="space-y-2">
                            {Array.isArray(columnData.most_common) ? (
                                // 数组格式：[[value, count], [value, count], ...]
                                columnData.most_common.map(([value, count], index) => (
                                    <div key={index} className="flex justify-between items-center">
                                        <span className="text-slate-300 truncate mr-4">{value}</span>
                                        <span className="text-sky-400 font-mono">{count}</span>
                                    </div>
                                ))
                            ) : (
                                // 对象格式：{value: count, value: count, ...}
                                Object.entries(columnData.most_common).map(([value, count], index) => (
                                    <div key={index} className="flex justify-between items-center">
                                        <span className="text-slate-300 truncate mr-4">{value}</span>
                                        <span className="text-sky-400 font-mono">{count}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };









    return (
        <div className="space-y-6">
            {/* 重要列快速选择 */}
            <div>
                <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold text-sky-300">重要列快速选择</h4>
                    <button
                        onClick={() => setShowColumnSelector(!showColumnSelector)}
                        className="text-sm text-sky-400 hover:text-sky-300"
                    >
                        {showColumnSelector ? '隐藏' : '显示'} 所有列
                    </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* 数值列 */}
                    {importantColumns.numeric.slice(0, 3).map(([name, data]) => 
                        renderColumnCard(name, data)
                    )}
                    
                    {/* 文本列 */}
                    {importantColumns.text.slice(0, 3).map(([name, data]) => 
                        renderColumnCard(name, data)
                    )}
                </div>
            </div>

            {/* 所有列选择器 */}
            {showColumnSelector && (
                <div>
                    <h4 className="font-semibold text-sky-300 mb-4">所有列</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 max-h-96 overflow-y-auto">
                        {allColumns.map(([name, data]) => 
                            renderColumnCard(name, data)
                        )}
                    </div>
                </div>
            )}

            {/* 可视化区域 */}
            {renderVisualization()}
        </div>
    );
};

const ProfilingReport = ({ report, dataSource }) => {
  if (!report) {
    return (
        <div className="text-center py-12 text-slate-400">
            <p>分析报告加载中或不可用...</p>
        </div>
    );
  }

  const isTextFile = report.analysis_type === 'text';
  const isTabularFile = report.analysis_type === 'tabular';
  const isImageFile = report.analysis_type === 'image';
  const tableStats = report.table;
  const tabularStats = report.basic_info;
  const textStats = report.text_stats;



  return (
    <div className="space-y-8 text-slate-200">
      
      {/* --- Data Overview --- */}
      <Section title="数据概览" icon={<span className="text-2xl">📊</span>}>
        {isTextFile && textStats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="词数统计" value={textStats.word_count?.toLocaleString() ?? 'N/A'} />
            <StatCard label="字符数" value={textStats.char_count?.toLocaleString() ?? 'N/A'} />
            <StatCard label="句子数" value={textStats.sentence_count?.toLocaleString() ?? 'N/A'} />
            <StatCard label="平均句长" value={textStats.avg_sentence_length ?? 'N/A'} />
            {textStats.unique_words && (
              <StatCard label="独特词汇" value={textStats.unique_words?.toLocaleString() ?? 'N/A'} />
            )}
            {textStats.lexical_diversity && (
              <StatCard label="词汇多样性" value={textStats.lexical_diversity ?? 'N/A'} />
            )}
            {textStats.avg_word_length && (
              <StatCard label="平均词长" value={textStats.avg_word_length ?? 'N/A'} />
            )}
            {textStats.readability_score && (
              <StatCard 
                label="可读性评分" 
                value={textStats.readability_score ?? 'N/A'} 
                className={
                  textStats.readability_score >= 60 ? "bg-green-500/10 border border-green-500/20" :
                  textStats.readability_score >= 30 ? "bg-yellow-500/10 border border-yellow-500/20" :
                  "bg-red-500/10 border border-red-500/20"
                }
              />
            )}
          </div>
        ) : isTabularFile && tabularStats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard label="行数" value={tabularStats.rows?.toLocaleString() ?? 'N/A'} />
            <StatCard label="列数" value={tabularStats.columns?.toLocaleString() ?? 'N/A'} />
            <StatCard label="内存使用" value={tabularStats.memory_usage ? `${(tabularStats.memory_usage / 1024).toFixed(2)} KB` : 'N/A'} />
            <StatCard label="重复行数" value={report.data_quality?.duplicate_rows?.toLocaleString() ?? 'N/A'} />
            <StatCard label="重复率" value={report.data_quality?.duplicate_percentage != null ? report.data_quality.duplicate_percentage.toFixed(2) + '%' : 'N/A'} />
          </div>
        ) : isImageFile && report.image_properties ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard label="宽度" value={report.image_properties.dimensions ? `${report.image_properties.dimensions.width} px` : 'N/A'} />
            <StatCard label="高度" value={report.image_properties.dimensions ? `${report.image_properties.dimensions.height} px` : 'N/A'} />
            <StatCard label="文件大小" value={report.image_properties.file_size_bytes ? `${(report.image_properties.file_size_bytes / 1024).toFixed(2)} KB` : 'N/A'} />
            <StatCard label="图像格式" value={report.image_properties.format ?? 'N/A'} />
            <StatCard label="颜色模式" value={report.image_properties.mode ?? 'N/A'} />
            <StatCard label="感知哈希" value={report.image_properties.phash ?? 'N/A'} />
          </div>
        ) : tableStats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard label="变量数量" value={tableStats.n_var ?? 'N/A'} />
            <StatCard label="观测值数量" value={tableStats.n?.toLocaleString() ?? 'N/A'} />
            <StatCard label="缺失单元格" value={tableStats.n_cells_missing?.toLocaleString() ?? 'N/A'} />
            <StatCard label="缺失率" value={tableStats.p_cells_missing != null ? (tableStats.p_cells_missing * 100).toFixed(2) + '%' : 'N/A'} />
            <StatCard label="重复行数" value={tableStats.n_duplicates?.toLocaleString() ?? 'N/A'} />
          </div>
        ) : (
            <p className='text-slate-400'>数据概览信息不可用。</p>
        )}
            </Section>

      {/* --- Image Analysis --- */}
      {isImageFile && (
        <Section title="图像分析报告" icon={<span className="text-2xl">🖼️</span>}>
          <ImageAnalysisReport result={report} filePath={dataSource?.file_path} />
        </Section>
      )}

      {/* --- Text Analysis --- */}
      {isTextFile && (
        <Section title="文本智能分析" icon={<span className="text-2xl">📄</span>}>
          <div className="space-y-6">
            
            {/* Keywords */}
            <div>
              <h4 className="font-semibold text-sky-300 mb-3">关键词提取</h4>
              <div className="space-y-3">
                <div className="flex flex-col gap-y-3">
                  {report.keywords?.length > 0 ? (
                    // Chunk the keywords into groups of 5 for structured display
                    Array.from({ length: Math.ceil(report.keywords.length / 5) }).map((_, chunkIndex) => (
                      <div key={chunkIndex} className="flex flex-wrap gap-x-2 gap-y-3">
                        {report.keywords.slice(chunkIndex * 5, chunkIndex * 5 + 5).map((keyword, index) => (
                          <div 
                            key={index} 
                            className="bg-sky-900/50 text-sky-300 text-sm font-medium px-4 py-1.5 rounded-full border border-sky-500/30 flex items-center gap-2 shadow-md hover:bg-sky-800/70 transition-colors duration-200"
                          >
                            <span className="font-semibold">{keyword}</span>
                            {report.keyword_scores && report.keyword_scores[keyword] && (
                              <span className="text-xs bg-sky-600/50 text-white px-2 py-0.5 rounded-md font-mono">
                                {report.keyword_scores[keyword]}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-400 italic">未提取到关键词</p>
                  )}
                </div>
                {report.analysis_quality && (
                  <div className="text-xs text-slate-400 mt-3">
                    提取了 {report.analysis_quality.keywords_extracted} 个关键词 • 
                    分析完整度: <span className="font-semibold text-sky-400">{report.analysis_quality.analysis_completeness}</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Sentiment Analysis */}
            <div>
              <h4 className="font-semibold text-sky-300 mb-3">情感分析</h4>
              {report.sentiment && Object.keys(report.sentiment).length > 0 ? (
                <div className="space-y-4">
                  {report.sentiment_interpretation && (
                    <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-700/50">
                      <span className="text-sm text-slate-400">情感倾向: </span>
                      <span className="text-white font-semibold">{report.sentiment_interpretation}</span>
                    </div>
                  )}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard className="bg-green-500/10 border border-green-500/20" label="正面" value={`${(report.sentiment.pos * 100).toFixed(1)}%`} />
                    <StatCard className="bg-yellow-500/10 border border-yellow-500/20" label="中性" value={`${(report.sentiment.neu * 100).toFixed(1)}%`} />
                    <StatCard className="bg-red-500/10 border border-red-500/20" label="负面" value={`${(report.sentiment.neg * 100).toFixed(1)}%`} />
                    <StatCard className="bg-purple-500/10 border border-purple-500/20" label="综合得分" value={report.sentiment.compound.toFixed(2)} />
                  </div>
                </div>
              ) : (
                <p className="text-slate-400 italic">情感分析数据不可用</p>
              )}
            </div>

            {/* Content Summary */}
            <div>
              <h4 className="font-semibold text-sky-300 mb-3">内容摘要</h4>
              <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {report.summary || <span className="italic">暂无内容摘要</span>}
                </p>
                {report.summary_sentences && report.summary_sentences.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <h5 className="text-sm text-slate-400 mb-2">摘要句子分解:</h5>
                    <ul className="space-y-1">
                      {report.summary_sentences.map((sentence, index) => (
                        <li key={index} className="text-sm text-slate-300 flex">
                          <span className="text-sky-400 mr-2">{index + 1}.</span>
                          <span>{sentence}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Content Insights */}
            {report.content_insights && (
              <div>
                <h4 className="font-semibold text-sky-300 mb-3">内容特征分析</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {report.content_insights.document_structure && (
                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                      <h5 className="text-sm font-semibold text-white mb-2">文档结构</h5>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">包含问句:</span>
                          <span className={report.content_insights.document_structure.has_questions ? "text-green-400" : "text-slate-500"}>
                            {report.content_insights.document_structure.has_questions ? "是" : "否"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">包含感叹句:</span>
                          <span className={report.content_insights.document_structure.has_exclamations ? "text-green-400" : "text-slate-500"}>
                            {report.content_insights.document_structure.has_exclamations ? "是" : "否"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">包含数字:</span>
                          <span className={report.content_insights.document_structure.has_numbers ? "text-green-400" : "text-slate-500"}>
                            {report.content_insights.document_structure.has_numbers ? "是" : "否"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">段落数:</span>
                          <span className="text-white">{report.content_insights.document_structure.paragraph_count}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {report.content_insights.language_characteristics && (
                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                      <h5 className="text-sm font-semibold text-white mb-2">语言特征</h5>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">检测语言:</span>
                          <span className="text-white">{report.content_insights.language_characteristics.detected_language}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">检测置信度:</span>
                          <span className="text-white">{report.content_insights.language_characteristics.language_confidence}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">混合语言:</span>
                          <span className={report.content_insights.language_characteristics.mixed_language ? "text-yellow-400" : "text-green-400"}>
                            {report.content_insights.language_characteristics.mixed_language ? "是" : "否"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* --- Tabular Analysis --- */}
      {isTabularFile && (
        <Section title="表格数据分析" icon={<span className="text-2xl">📊</span>}>
          <div className="space-y-6">
            
            {/* Data Quality */}
            {report.data_quality && (
              <div>
                <h4 className="font-semibold text-sky-300 mb-3">数据质量评估</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                    <h5 className="text-sm font-semibold text-white mb-2">缺失值统计</h5>
                    <div className="space-y-1 text-sm max-h-40 overflow-y-auto">
                      {Object.entries(report.data_quality.missing_values || {}).map(([col, count]) => (
                        <div key={col} className="flex justify-between">
                          <span className="text-slate-400 truncate mr-2">{col}:</span>
                          <span className={count > 0 ? "text-red-400" : "text-green-400"}>
                            {count} ({report.data_quality.missing_percentage?.[col]?.toFixed(1)}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                    <h5 className="text-sm font-semibold text-white mb-2">数据类型分布</h5>
                    <div className="space-y-1 text-sm">
                      {Object.entries(report.dtype_distribution || {}).map(([dtype, count]) => (
                        <div key={dtype} className="flex justify-between">
                          <span className="text-slate-400">{dtype}:</span>
                          <span className="text-white">{count} 列</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Insights */}
            {report.insights && report.insights.length > 0 && (
              <div>
                <h4 className="font-semibold text-sky-300 mb-3">数据洞察</h4>
                <div className="space-y-2">
                  {report.insights.map((insight, index) => (
                    <div key={index} className="bg-slate-800/30 p-3 rounded-lg border border-slate-700/50">
                      <div className="flex items-start gap-2">
                        <span className="text-sky-400 mt-1">•</span>
                        <span className="text-slate-300">{insight}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Column Analysis Summary */}
            {report.column_analysis && (
              <div>
                <h4 className="font-semibold text-sky-300 mb-3">列分析摘要</h4>
                <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <StatCard 
                      label="数值列" 
                      value={Object.values(report.column_analysis).filter(col => col.dtype?.includes('int') || col.dtype?.includes('float')).length}
                      className="bg-blue-500/10 border border-blue-500/20"
                    />
                    <StatCard 
                      label="文本列" 
                      value={Object.values(report.column_analysis).filter(col => col.dtype === 'object').length}
                      className="bg-green-500/10 border border-green-500/20"
                    />
                    <StatCard 
                      label="高基数列" 
                      value={Object.values(report.column_analysis).filter(col => col.unique_percentage > 95).length}
                      className="bg-yellow-500/10 border border-yellow-500/20"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* --- Interactive Column Analysis --- */}
      {isTabularFile && report.column_analysis && (
        <Section title="交互式列分析" icon={<span className="text-2xl">📊</span>}>
          <InteractiveColumnAnalysis columnAnalysis={report.column_analysis} />
        </Section>
      )}

      {/* --- Variable Details for legacy table data --- */}
      {!isTextFile && !isTabularFile && report.variables && (
        <Section title="变量详情" icon={<span className="text-2xl">🔬</span>}>
          <div className="bg-slate-900/70 rounded-xl overflow-hidden border border-slate-700/50">
            <SyntaxHighlighter 
              language="json" 
              style={vscDarkPlus} 
              customStyle={{ background: 'transparent', padding: '1.5rem', margin: 0, fontSize: '0.875rem' }}
              wrapLongLines={true}
            >
              {JSON.stringify(report.variables, null, 2)}
            </SyntaxHighlighter>
          </div>
        </Section>
      )}
    </div>
  );
};

export default ProfilingReport; 