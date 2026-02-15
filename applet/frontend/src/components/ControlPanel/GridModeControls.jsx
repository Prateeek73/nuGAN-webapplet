/**
 * Grid Mode Controls - Mass selection and number of rows
 */
import React from 'react';
import { NU_VALUES, MASS_LIMITS, NUM_MAPS_OPTIONS } from '../../config';

function GridModeControls({
  selectedMasses,
  customGridMass,
  numRows,
  gridMassError,
  onToggleMass,
  onCustomMassChange,
  onAddCustomMass,
  onRemoveCustomMass,
  onNumRowsChange,
}) {
  return (
    <>
      <div className="panel-section">
        <h2 className="section-title">Select Masses</h2>
        <div className="chip-group">
          {NU_VALUES.map(mass => (
            <button
              key={mass}
              className={`chip ${selectedMasses.includes(mass) ? 'selected' : ''}`}
              onClick={() => onToggleMass(mass)}
            >
              {mass.toFixed(2)} eV
            </button>
          ))}
        </div>
        
        {/* Custom masses display */}
        {selectedMasses.filter(m => !NU_VALUES.includes(m)).length > 0 && (
          <div className="custom-masses">
            <span className="custom-mass-label">Custom:</span>
            {selectedMasses.filter(m => !NU_VALUES.includes(m)).map(mass => (
              <span key={mass} className="custom-mass-tag">
                {mass.toFixed(2)} eV
                <button 
                  className="remove-mass-btn"
                  onClick={() => onRemoveCustomMass(mass)}
                >×</button>
              </span>
            ))}
          </div>
        )}
        
        {/* Add custom mass */}
        <div className="input-group add-custom-mass">
          <label>Add Custom Mass ({MASS_LIMITS.min.toFixed(2)} - {MASS_LIMITS.max.toFixed(2)} eV)</label>
          <div className="input-with-button">
            <input
              type="number"
              className={`input-field ${gridMassError ? 'input-error' : ''}`}
              value={customGridMass}
              onChange={(e) => onCustomMassChange(e.target.value)}
              step="0.01"
              min={MASS_LIMITS.min}
              max={MASS_LIMITS.max}
              placeholder="e.g. 0.35"
            />
            <button 
              className="btn-add"
              onClick={onAddCustomMass}
              disabled={!customGridMass}
            >
              Add
            </button>
          </div>
          {gridMassError && <span className="error-text">{gridMassError}</span>}
        </div>
      </div>

      <div className="panel-section">
        <h2 className="section-title">Number of Samples (Rows)</h2>
        <select
          className="select-field"
          value={numRows}
          onChange={(e) => onNumRowsChange(parseInt(e.target.value))}
        >
          {NUM_MAPS_OPTIONS.map(num => (
            <option key={num} value={num}>{num}</option>
          ))}
        </select>
        <p className="hint">Each row uses same seed across all masses</p>
      </div>
    </>
  );
}

export default GridModeControls;
