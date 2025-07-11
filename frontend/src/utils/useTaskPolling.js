import { useState, useCallback, useRef } from 'react';
import * as api from '../services/api';

export const useTaskPolling = () => {
    const [taskId, setTaskId] = useState(null);
    const [taskStatus, setTaskStatus] = useState(null);
    const [taskResult, setTaskResult] = useState(null);
    const [taskError, setTaskError] = useState(null);
    const pollingRef = useRef(null);

    const stopPolling = () => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    };

    const poll = useCallback(async (currentTaskId) => {
        try {
            const response = await api.getTaskStatus(currentTaskId);
            const { status, result, error } = response.data;

            setTaskStatus(status.toLowerCase());

            if (status === 'SUCCESS' || status === 'completed') {
                setTaskResult(result.report_json || result);
                setTaskStatus('completed');
                stopPolling();
            } else if (status === 'FAILURE' || status === 'failed') {
                setTaskError(error || '任务执行失败');
                setTaskStatus('failed');
                stopPolling();
            }
        } catch (err) {
            console.error('Polling error:', err);
            setTaskError(err.response?.data?.detail || '轮询任务状态时发生网络错误。');
            stopPolling();
        }
    }, []);

    const startPolling = useCallback((newTaskId) => {
        stopPolling(); 
        setTaskId(newTaskId);
        setTaskStatus('pending');
        setTaskResult(null);
        setTaskError(null);

        pollingRef.current = setInterval(() => {
            poll(newTaskId);
        }, 3000);

        // Cleanup on unmount
        return stopPolling;
    }, [poll]);

    const resetTask = useCallback(() => {
        stopPolling();
        setTaskId(null);
        setTaskStatus(null);
        setTaskResult(null);
        setTaskError(null);
    }, []);

    return { taskId, taskStatus, taskResult, taskError, startPolling, resetTask };
};