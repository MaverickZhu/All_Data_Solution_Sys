import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../services/api';
import ProfilingReport from '../components/ProfilingReport';
import { useTaskPolling } from '../utils/useTaskPolling';

const DataSourceDetail = () => {
    // 从URL中获取ID
    const { id: dataSourceId } = useParams(); 
    
    const [dataSource, setDataSource] = useState(null);
    const [startError, setStartError] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    // 使用自定义Hook进行轮询
    const { 
        taskId, 
        taskStatus, 
        taskResult, 
        taskError, 
        startPolling, 
        resetTask 
    } = useTaskPolling(dataSourceId);

    useEffect(() => {
        const fetchDataSource = async () => {
            if (!dataSourceId) return;
            setIsLoading(true);
            try {
                const response = await api.getDataSourceDetail(dataSourceId);
                setDataSource(response.data);
                // 如果后端已经有任务信息，则直接开始轮询
                if (response.data.profiling_task_id && response.data.profiling_status !== 'completed') {
                    startPolling(response.data.profiling_task_id);
                }
            } catch (error) {
                console.error('Failed to fetch data source details:', error);
                setStartError('无法加载数据源详情。');
            } finally {
                setIsLoading(false);
            }
        };

        fetchDataSource();
    }, [dataSourceId, startPolling]);

    const handleStartProfiling = async () => {
        if (!dataSource?.project_id) {
            setStartError('项目ID未知，无法开始分析。');
            return;
        }
        setStartError('');
        resetTask(); // 重置上一次的任务状态
        try {
            const response = await api.startDataProfiling(dataSourceId, dataSource.project_id);
            const newTaskId = response.data.task_id;
            if (newTaskId) {
                startPolling(newTaskId); // 启动轮询
            } else {
                setStartError('未能从后端获取任务ID。');
            }
        } catch (error) {
            console.error('Failed to start data profiling:', error);
            setStartError(error.response?.data?.detail || '启动数据分析失败，请检查控制台获取详情。');
        }
    };
    
    // 从后端获取的最新分析结果
    const latestReportString = taskResult || (dataSource?.profiling_status === 'completed' ? dataSource.profiling_result : null);
    let latestReport = null;
    if (latestReportString) {
        try {
            latestReport = JSON.parse(latestReportString);
        } catch (e) {
            console.error("Failed to parse profiling report JSON:", e);
        }
    }

    if (isLoading) {
        return <div>加载中...</div>;
    }

    if (!dataSource) {
        return <div>找不到数据源。</div>;
    }

    return (
        <div style={{ padding: '20px' }}>
            <h1>数据源详情: {dataSource.name}</h1>
            <p><strong>ID:</strong> {dataSource.id}</p>
            <p><strong>类型:</strong> {dataSource.type}</p>
            <p><strong>所属项目ID:</strong> {dataSource.project_id}</p>
            <hr />

            <h2>数据分析</h2>
            <button 
                onClick={handleStartProfiling} 
                disabled={taskStatus === 'pending' || taskStatus === 'running'}
                style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
            >
                {taskStatus === 'pending' || taskStatus === 'running' ? '分析中...' : '开始数据分析'}
            </button>
            
            {startError && <p style={{ color: 'red' }}>{startError}</p>}
            {taskError && <p style={{ color: 'red' }}>轮询错误: {taskError}</p>}

            {/* 结果展示区 */}
            {latestReport && (
                <div style={{ marginTop: '20px' }}>
                    <h3>分析报告</h3>
                    <ProfilingReport report={latestReport} />
                </div>
            )}
        </div>
    );
};

export default DataSourceDetail; 