/**
 * Custom hook for colormap application logic
 */
import { useState, useEffect } from 'react';
import { applyColormap } from '../utils/colormaps';

export function useColormap({
  colormap,
  gridMode,
  rawImages,
  rawGridData,
  setGeneratedImages,
  setGridData,
}) {
  const [isApplyingColormap, setIsApplyingColormap] = useState(false);

  useEffect(() => {
    const applyColormapToAll = async () => {
      if (rawImages.length === 0 && !rawGridData) return;
      
      setIsApplyingColormap(true);
      
      try {
        if (!gridMode && rawImages.length > 0) {
          const newImages = await Promise.all(
            rawImages.map(async (img) => ({
              ...img,
              image: await applyColormap(img.grayscale, colormap)
            }))
          );
          setGeneratedImages(newImages);
        } else if (gridMode && rawGridData) {
          const newGrid = await Promise.all(
            rawGridData.grid.map(async (row) => ({
              ...row,
              maps: await Promise.all(
                row.maps.map(async (cell) => ({
                  ...cell,
                  image: await applyColormap(cell.grayscale, colormap)
                }))
              )
            }))
          );
          setGridData({
            ...rawGridData,
            grid: newGrid,
            colormap: colormap
          });
        }
      } catch (err) {
        console.error('Error applying colormap:', err);
      } finally {
        setIsApplyingColormap(false);
      }
    };

    applyColormapToAll();
  }, [colormap, rawImages, rawGridData, gridMode, setGeneratedImages, setGridData]);

  return { isApplyingColormap };
}

export default useColormap;
