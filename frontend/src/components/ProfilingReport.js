import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';


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

const ProfilingReport = ({ report, dataSource }) => {
  if (!report) {
    return (
        <div className="text-center py-12 text-slate-400">
            <p>分析报告加载中或不可用...</p>
        </div>
    );
  }

  const isTextFile = report.analysis_type === 'text';
  const tableStats = report.table;
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

      {/* --- Variable Details for table data --- */}
      {!isTextFile && report.variables && (
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