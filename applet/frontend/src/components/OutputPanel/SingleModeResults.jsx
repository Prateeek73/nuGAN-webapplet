/**
 * Single Mode Results - Image grid for single mass generation
 */
import React from 'react';
import { COLORMAPS } from '../../config';

function SingleModeResults({
  generatedImages,
  nuValue,
  colormap,
  usedSeed,
  generateTime,
  onImageClick,
}) {
  if (generatedImages.length === 0) return null;

  return (
    <>
      <div className="results-info">
        <span>mν = {nuValue.toFixed(2)} eV</span>
        <span>{generatedImages.length} maps</span>
        <span>Colormap: {COLORMAPS.find(c => c.id === colormap)?.name}</span>
        {usedSeed && <span>Seed: {usedSeed}</span>}
        {generateTime && <span className="time-info">⏱ {generateTime}s</span>}
      </div>

      <div className="image-grid">
        {generatedImages.map((img, idx) => (
          <div 
            key={idx} 
            className="image-card"
            onClick={() => onImageClick({ ...img, index: idx, nuValue, seed: usedSeed })}
          >
            <img src={img.image} alt={`Map ${idx + 1}`} />
            <div className="cell-stats-full">
              <div className="cell-stat-row">
                <span>Min: {img.stats.min.toFixed(3)}</span>
                <span>Max: {img.stats.max.toFixed(3)}</span>
              </div>
              <div className="cell-stat-row">
                <span>Mean: {img.stats.mean.toFixed(3)}</span>
                <span>Std: {img.stats.std.toFixed(3)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

export default SingleModeResults;
