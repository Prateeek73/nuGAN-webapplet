/**
 * Model Loader component - Load model button and status
 */
import React from 'react';

function ModelLoader({ 
  modelLoaded, 
  isLoading, 
  modelLoadTime, 
  onLoadModel 
}) {
  return (
    <div className="panel-section">
      <h2 className="section-title">Model</h2>
      <button 
        className={`btn btn-primary ${modelLoaded ? 'btn-success' : ''}`}
        onClick={onLoadModel}
        disabled={isLoading || modelLoaded}
      >
        {isLoading ? 'Loading...' : modelLoaded ? '✓ Model Loaded' : 'Load Model'}
      </button>
      <div className="status-badge">
        <span className={`status-dot ${modelLoaded ? 'active' : ''}`}></span>
        {modelLoaded ? 'Ready' : 'Not loaded'}
        {modelLoadTime && <span className="time-badge">({modelLoadTime}s)</span>}
      </div>
    </div>
  );
}

export default ModelLoader;
