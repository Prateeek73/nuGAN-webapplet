/**
 * Custom hook for map generation logic
 */
import { useState, useCallback } from 'react';
import { generateMaps, generateGrid, createCancelToken, cancelRequest } from '../services/api';

export function useGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateTime, setGenerateTime] = useState(null);
  const [usedSeed, setUsedSeed] = useState(null);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [rawImages, setRawImages] = useState([]);
  const [gridData, setGridData] = useState(null);
  const [rawGridData, setRawGridData] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = useCallback(async ({
    modelLoaded,
    gridMode,
    selectedMasses,
    numRows,
    colormap,
    nuValue,
    numMaps,
  }) => {
    if (!modelLoaded) {
      setError('Please load the model first');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedImages([]);
    setGridData(null);
    setGenerateTime(null);

    const startTime = performance.now();
    const signal = createCancelToken('generate');

    try {
      if (gridMode) {
        const response = await generateGrid({
          nuValues: selectedMasses,
          numRows: numRows,
          colormap: colormap
        }, signal);

        const endTime = performance.now();
        const genTime = ((endTime - startTime) / 1000).toFixed(2);

        if (response.status === 'success') {
          setGridData(response);
          setRawGridData(response);
          setGenerateTime(genTime);
          setUsedSeed(response.base_seed);
        } else {
          setError(response.message || 'Generation failed');
        }
      } else {
        const response = await generateMaps({
          nuValue: nuValue,
          numMaps: numMaps,
          colormap: colormap
        }, signal);

        const endTime = performance.now();
        const genTime = ((endTime - startTime) / 1000).toFixed(2);

        if (response.status === 'success') {
          setGeneratedImages(response.images);
          setRawImages(response.images);
          setGenerateTime(genTime);
          setUsedSeed(response.seed);
        } else {
          setError(response.message || 'Generation failed');
        }
      }
    } catch (err) {
      if (err.name === 'AbortError' || err.message === 'canceled') {
        return;
      }
      setError(err.message || 'Failed to generate maps');
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const handleCancelGeneration = useCallback(() => {
    cancelRequest('generate');
    setIsGenerating(false);
    setError('Generation cancelled');
  }, []);

  return {
    isGenerating,
    generateTime,
    usedSeed,
    generatedImages,
    setGeneratedImages,
    rawImages,
    gridData,
    setGridData,
    rawGridData,
    error,
    setError,
    handleGenerate,
    handleCancelGeneration,
  };
}

export default useGeneration;
