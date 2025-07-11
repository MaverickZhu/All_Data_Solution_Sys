import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsVisualization = ({ columnName, columnData, chartType = 'histogram' }) => {
    // 检查输入参数
    if (!columnName || !columnData) {
        return (
            <div className="h-64 flex items-center justify-center bg-slate-800/30 rounded-lg border border-slate-700/50">
                <div className="text-center">
                    <div className="text-slate-400 mb-2">📊</div>
                    <div className="text-slate-300">缺少必要的数据</div>
                </div>
            </div>
        );
    }
    
    const isNumeric = columnData.dtype?.includes('int') || columnData.dtype?.includes('float');
    
    // 生成直方图配置
    const getHistogramOption = () => {
        const { min, max, mean } = columnData;
        
        if (min === undefined || max === undefined) {
            return null;
        }
        
        // 创建分组数据（简化版，实际应该从后端获取）
        const binCount = 10;
        const binWidth = (max - min) / binCount;
        const bins = [];
        
        for (let i = 0; i < binCount; i++) {
            const binStart = min + i * binWidth;
            const binEnd = min + (i + 1) * binWidth;
            bins.push({
                name: `${binStart.toFixed(2)}-${binEnd.toFixed(2)}`,
                value: Math.floor(Math.random() * 100) + 10, // 模拟数据，实际应从后端获取
                binStart,
                binEnd
            });
        }
        
        return {
            title: {
                text: `${columnName} 数据分布`,
                textStyle: {
                    color: '#e2e8f0',
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                borderColor: '#374151',
                textStyle: {
                    color: '#e2e8f0'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: bins.map(bin => bin.name),
                axisLabel: {
                    color: '#9ca3af',
                    rotate: 45
                },
                axisLine: {
                    lineStyle: {
                        color: '#4b5563'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '频次',
                nameTextStyle: {
                    color: '#9ca3af'
                },
                axisLabel: {
                    color: '#9ca3af'
                },
                axisLine: {
                    lineStyle: {
                        color: '#4b5563'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#374151'
                    }
                }
            },
            series: [
                {
                    name: '频次',
                    type: 'bar',
                    data: bins.map(bin => bin.value),
                    itemStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [{
                                offset: 0, color: '#0ea5e9'
                            }, {
                                offset: 1, color: '#0284c7'
                            }]
                        }
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#38bdf8'
                        }
                    },
                    // 添加统计标记线
                    ...(mean !== undefined && {
                        markLine: {
                            silent: true,
                            lineStyle: {
                                color: '#ef4444',
                                width: 2,
                                type: 'dashed'
                            },
                            data: [
                                {
                                    name: '均值',
                                    xAxis: Math.max(0, bins.findIndex(bin => bin && mean >= bin.binStart && mean <= bin.binEnd)),
                                    label: {
                                        formatter: `均值: ${mean}`,
                                        color: '#ef4444'
                                    }
                                }
                            ]
                        }
                    })
                }
            ]
        };
    };
    
    // 生成箱线图配置
    const getBoxPlotOption = () => {
        const { min, max, median, quartiles } = columnData;
        
        if (!quartiles || min === undefined || max === undefined || median === undefined) {
            return null;
        }
        
        const boxData = [
            [min, quartiles.q25 || min, median, quartiles.q75 || max, max]
        ];
        
        return {
            title: {
                text: `${columnName} 箱线图`,
                textStyle: {
                    color: '#e2e8f0',
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                borderColor: '#374151',
                textStyle: {
                    color: '#e2e8f0'
                },
                formatter: function(params) {
                    const data = params.data;
                    if (!data || !Array.isArray(data) || data.length < 5) {
                        return `<div style="padding: 8px;"><strong>${columnName}</strong><br/>数据不可用</div>`;
                    }
                    return `
                        <div style="padding: 8px;">
                            <div><strong>${columnName}</strong></div>
                            <div>最小值: ${data[0]}</div>
                            <div>Q1: ${data[1]}</div>
                            <div>中位数: ${data[2]}</div>
                            <div>Q3: ${data[3]}</div>
                            <div>最大值: ${data[4]}</div>
                        </div>
                    `;
                }
            },
            grid: {
                left: '10%',
                right: '10%',
                bottom: '15%'
            },
            xAxis: {
                type: 'category',
                data: [columnName],
                axisLabel: {
                    color: '#9ca3af'
                },
                axisLine: {
                    lineStyle: {
                        color: '#4b5563'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '数值',
                nameTextStyle: {
                    color: '#9ca3af'
                },
                axisLabel: {
                    color: '#9ca3af'
                },
                axisLine: {
                    lineStyle: {
                        color: '#4b5563'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#374151'
                    }
                }
            },
            series: [
                {
                    name: 'boxplot',
                    type: 'boxplot',
                    data: boxData,
                    itemStyle: {
                        color: '#0ea5e9',
                        borderColor: '#0284c7'
                    }
                }
            ]
        };
    };
    
    // 生成饼图配置
    const getPieChartOption = () => {
        if (!columnData.most_common) {
            return null;
        }
        
        // 处理不同格式的most_common数据
        let pieData = [];
        
        if (Array.isArray(columnData.most_common)) {
            // 如果是数组格式：[[value, count], [value, count], ...]
            pieData = columnData.most_common.map(([value, count], index) => ({
                value: count || 0,
                name: String(value || 'Unknown'),
                itemStyle: {
                    color: [
                        '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                        '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
                    ][index % 10]
                }
            }));
        } else if (typeof columnData.most_common === 'object') {
            // 如果是对象格式：{value: count, value: count, ...}
            pieData = Object.entries(columnData.most_common).map(([value, count], index) => ({
                value: count || 0,
                name: String(value || 'Unknown'),
                itemStyle: {
                    color: [
                        '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                        '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
                    ][index % 10]
                }
            }));
        } else {
            return null;
        }
        
        return {
            title: {
                text: `${columnName} 值分布`,
                textStyle: {
                    color: '#e2e8f0',
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                borderColor: '#374151',
                textStyle: {
                    color: '#e2e8f0'
                },
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                right: 10,
                top: 20,
                bottom: 20,
                textStyle: {
                    color: '#9ca3af'
                }
            },
            series: [
                {
                    name: columnName,
                    type: 'pie',
                    radius: '50%',
                    center: ['40%', '50%'],
                    data: pieData,
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
    };
    
    // 根据图表类型获取配置
    const getOption = () => {
        switch (chartType) {
            case 'histogram':
                return isNumeric ? getHistogramOption() : null;
            case 'box':
                return isNumeric ? getBoxPlotOption() : null;
            case 'pie':
                return !isNumeric ? getPieChartOption() : null;
            default:
                return null;
        }
    };
    
    const option = getOption();
    
    if (!option) {
        return (
            <div className="h-64 flex items-center justify-center bg-slate-800/30 rounded-lg border border-slate-700/50">
                <div className="text-center">
                    <div className="text-slate-400 mb-2">📊</div>
                    <div className="text-slate-300">
                        {chartType === 'histogram' && !isNumeric && '直方图仅适用于数值型数据'}
                        {chartType === 'box' && !isNumeric && '箱线图仅适用于数值型数据'}
                        {chartType === 'pie' && isNumeric && '饼图仅适用于分类数据'}
                        {!option && '暂无可用数据'}
                    </div>
                </div>
            </div>
        );
    }
    
    return (
        <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
            <ReactECharts
                key={`${columnName}-${chartType}`}
                option={option}
                style={{ height: '400px' }}
                theme="dark"
                opts={{ renderer: 'canvas' }}
                notMerge={true}
                lazyUpdate={true}
            />
            
            {/* 添加数据解读 */}
            <div className="mt-4 p-3 bg-slate-800/30 rounded-lg border border-slate-600/30">
                <div className="text-xs text-slate-400">
                    <div className="mb-1">📊 图表解读：</div>
                    {chartType === 'histogram' && isNumeric && (
                        <div className="text-slate-300">
                            <div>• 显示数据的分布情况和频次</div>
                            <div>• 均值: {columnData.mean || 'N/A'}，中位数: {columnData.median || 'N/A'}</div>
                            <div>• 标准差: {columnData.std || 'N/A'}</div>
                        </div>
                    )}
                    {chartType === 'box' && isNumeric && (
                        <div className="text-slate-300">
                            <div>• 显示数据的五数概括：最小值、Q1、中位数、Q3、最大值</div>
                            <div>• 中间50%的数据分布在Q1({columnData.quartiles?.q25})到Q3({columnData.quartiles?.q75})之间</div>
                            <div>• 可以识别异常值和数据分布的偏斜情况</div>
                        </div>
                    )}
                    {chartType === 'pie' && !isNumeric && (
                        <div className="text-slate-300">
                            <div>• 显示不同类别的占比情况</div>
                            <div>• 总共有 {columnData.unique_count} 个不同的值</div>
                            <div>• 最常见的值: {
                                Array.isArray(columnData.most_common) ? 
                                    `${columnData.most_common?.[0]?.[0]} (出现 ${columnData.most_common?.[0]?.[1]} 次)` :
                                    typeof columnData.most_common === 'object' ? 
                                        (() => {
                                            const entries = Object.entries(columnData.most_common);
                                            return entries.length > 0 ? `${entries[0][0]} (出现 ${entries[0][1]} 次)` : 'N/A';
                                        })() :
                                        'N/A'
                            }</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EChartsVisualization; 