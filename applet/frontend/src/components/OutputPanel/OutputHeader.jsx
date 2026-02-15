/**
 * Output Header component - Title, colormap selector, download button
 */
import React from 'react';
import { COLORMAPS } from '../../config';

function OutputHeader({
  colormap,
  isApplyingColormap,
  hasResults,
  onColormapChange,
  onDownloadAll,
}) {
  return (
    <div className="output-header">
      <h2 className="output-title">Generated Output</h2>
      <div className="output-controls">
        <label className="colormap-label">Colormap:</label>
        <select 
          className="colormap-select"
          value={colormap}
          onChange={(e) => onColormapChange(e.target.value)}
          disabled={isApplyingColormap}
        >
          {COLORMAPS.map(cmap => (
            <option key={cmap.id} value={cmap.id}>{cmap.name}</option>
          ))}
        </select>
        {isApplyingColormap && <span className="colormap-loading">Applying...</span>}
        {hasResults && (
          <button className="btn-download" onClick={onDownloadAll}>
            ⬇ Download All
          </button>
        )}
      </div>
    </div>
  );
}

export default OutputHeader;
