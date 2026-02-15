/**
 * Grid Mode Results - Grid view for multiple mass comparison
 */
import React from 'react';
import { COLORMAPS } from '../../config';

function GridModeResults({
  gridData,
  generateTime,
  onImageClick,
}) {
  if (!gridData) return null;

  return (
    <>
      <div className="results-info">
        <span>Masses: {gridData.nu_values.map(v => v.toFixed(2) + ' eV').join(', ')}</span>
        <span>{gridData.num_rows} samples</span>
        <span>Colormap: {COLORMAPS.find(c => c.id === gridData.colormap)?.name}</span>
        {gridData.base_seed && <span>Base Seed: {gridData.base_seed}</span>}
        {generateTime && <span className="time-info">⏱ {generateTime}s</span>}
      </div>
      
      <div className="grid-container">
        <div className="grid-header">
          <div className="grid-corner"></div>
          {gridData.nu_values.map(nu => (
            <div key={nu} className="grid-col-header">
              mν = {nu.toFixed(2)} eV
            </div>
          ))}
        </div>
        
        {gridData.grid.map((row, rowIdx) => (
          <div key={rowIdx} className="grid-row">
            <div className="grid-row-header">
              Sample {rowIdx + 1}
              <span className="seed-label">seed: {row.seed}</span>
            </div>
            {row.maps.map((cell, colIdx) => (
              <div 
                key={colIdx} 
                className="grid-cell"
                onClick={() => onImageClick({ 
                  ...cell, 
                  index: rowIdx * gridData.nu_values.length + colIdx,
                  sampleNumber: rowIdx + 1,
                  nuValue: cell.nu_value,
                  seed: row.seed
                })}
              >
                <img src={cell.image} alt={`${cell.nu_value}eV sample ${rowIdx + 1}`} />
                <div className="cell-stats-full">
                  <div className="cell-stat-row">
                    <span>Min: {cell.stats.min.toFixed(3)}</span>
                    <span>Max: {cell.stats.max.toFixed(3)}</span>
                  </div>
                  <div className="cell-stat-row">
                    <span>Mean: {cell.stats.mean.toFixed(3)}</span>
                    <span>Std: {cell.stats.std.toFixed(3)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </>
  );
}

export default GridModeResults;
