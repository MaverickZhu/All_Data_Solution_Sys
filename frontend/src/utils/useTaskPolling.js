import { useState, useEffect, useRef } from 'react';
import { getTaskStatus } from '../services/api';

const POLLING_INTERVAL = 3000; // 3 seconds

export const useTaskPolling = (taskId) => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  const intervalRef = useRef(null);

  useEffect(() => {
    const stopPolling = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        setIsPolling(false);
      }
    };

    const poll = async () => {
      if (!taskId) return;
      try {
        const response = await getTaskStatus(taskId);
        const status = response.data.profiling_status;
        setTaskStatus(response.data);

        if (status === 'completed' || status === 'failed') {
          stopPolling();
        }
      } catch (err) {
        console.error('Polling failed:', err);
        setError('Failed to get task status.');
        stopPolling();
      }
    };

    if (taskId) {
      setIsPolling(true);
      // Immediately check status, then start interval
      poll(); 
      intervalRef.current = setInterval(poll, POLLING_INTERVAL);
    }

    // Cleanup function to stop polling when the component unmounts or taskId changes
    return () => {
      stopPolling();
    };
  }, [taskId]);

  return { taskStatus, error, isPolling };
}; 