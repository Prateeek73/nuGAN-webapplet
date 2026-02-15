/**
 * Mode Toggle component - Single/Grid mode switch
 */
import React from 'react';

function ModeToggle({ gridMode, onModeChange }) {
  return (
    <div className="panel-section">
      <h2 className="section-title">Generation Mode</h2>
      <div className="toggle-group">
        <button 
          className={`toggle-btn ${!gridMode ? 'active' : ''}`}
          onClick={() => onModeChange(false)}
        >
          Single Mass
        </button>
        <button 
          className={`toggle-btn ${gridMode ? 'active' : ''}`}
          onClick={() => onModeChange(true)}
        >
          Grid View
        </button>
      </div>
    </div>
  );
}

export default ModeToggle;
