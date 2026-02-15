/**
 * Loading State component - Shown during generation
 */
import React from 'react';

function LoadingState({ message, hint }) {
  return (
    <div className="loading-state">
      <div className="spinner"></div>
      <p>{message}</p>
      {hint && <p className="loading-hint">{hint}</p>}
    </div>
  );
}

export default LoadingState;
