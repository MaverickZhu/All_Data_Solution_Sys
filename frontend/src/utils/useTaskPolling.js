import { useState, useEffect, useRef, useCallback } from 'react';
import * as api from '../services/api';

export const useTaskPolling = (dataSourceId) => {
    const [taskId, setTaskId] = useState(null);
    const [taskStatus, setTaskStatus] = useState(null);
    const [taskResult, setTaskResult] = useState(null);
    const [taskError, setTaskError] = useState(null);
    
    const pollingRef = useRef(null);

    const stopPolling = useCallback(() => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    }, []);

    const pollStatus = useCallback(async (currentTaskId) => {
        try {
            const response = await api.getTaskStatus(currentTaskId);
            const { profiling_status, profiling_result } = response.data;

            setTaskStatus(profiling_status);
            setTaskError(null);

            if (profiling_status === 'completed') {
                setTaskResult(profiling_result);
                stopPolling();
            } else if (profiling_status === 'failed') {
                setTaskError('分析���务失败，请查看后端日志。');
                stopPolling();
            }
        } catch (error) {
            console.error('Polling error:', error);
            setTaskError('轮询任务状态时出错。');
            stopPolling();
        }
    }, [stopPolling]);

    const startPolling = useCallback((newTaskId) => {
        stopPolling(); // Ensure no multiple polls are running
        setTaskId(newTaskId);
        setTaskStatus('pending');
        setTaskResult(null);
        setTaskError(null);

        pollingRef.current = setInterval(() => {
            pollStatus(newTaskId);
        }, 3000); // Poll every 3 seconds
    }, [pollStatus, stopPolling]);

    const resetTask = useCallback(() => {
        stopPolling();
        setTaskId(null);
        setTaskStatus(null);
        setTaskResult(null);
        setTaskError(null);
    }, [stopPolling]);

    useEffect(() => {
        // Cleanup on unmount
        return () => {
            stopPolling();
        };
    }, [stopPolling]);

    return {
        taskId,
        taskStatus,
        taskResult,
        taskError,
        startPolling,
        resetTask,
    };
};