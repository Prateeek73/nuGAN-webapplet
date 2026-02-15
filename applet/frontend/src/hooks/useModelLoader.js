/**
 * Custom hook for model loading logic
 */
import { useState, useCallback, useEffect } from 'react';
import { loadModel, getModelStatus, createCancelToken } from '../services/api';

export function useModelLoader() {
  const [modelLoaded, setModelLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingModel, setIsCheckingModel] = useState(true);
  const [modelLoadTime, setModelLoadTime] = useState(null);
  const [error, setError] = useState(null);

  // Check if model is already loaded on mount
  useEffect(() => {
    const checkModelStatus = async () => {
      try {
        const status = await getModelStatus();
        if (status.model_loaded) {
          setModelLoaded(true);
        }
      } catch (err) {
        console.log('Server not available yet');
      } finally {
        setIsCheckingModel(false);
      }
    };
    checkModelStatus();
  }, []);

  const handleLoadModel = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setModelLoadTime(null);
    
    const startTime = performance.now();
    const signal = createCancelToken('loadModel');
    
    try {
      const response = await loadModel(null, signal);
      
      const endTime = performance.now();
      const loadTime = ((endTime - startTime) / 1000).toFixed(2);
      
      if (response.status === 'success') {
        setModelLoaded(true);
        setModelLoadTime(loadTime);
      } else {
        setError(response.message || 'Failed to load model');
      }
    } catch (err) {
      if (err.name === 'AbortError' || err.message === 'canceled') {
        return;
      }
      setError(err.message || 'Failed to connect to server');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    modelLoaded,
    isLoading,
    isCheckingModel,
    modelLoadTime,
    error,
    setError,
    handleLoadModel,
  };
}

export default useModelLoader;
