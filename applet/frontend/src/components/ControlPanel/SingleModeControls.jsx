/**
 * Single Mode Controls - Slider and number of maps selector
 */
import React from 'react';
import { NU_VALUES, MASS_LIMITS, NUM_MAPS_OPTIONS } from '../../config';

function SingleModeControls({
  nuValue,
  customNuValue,
  numMaps,
  massError,
  onSliderChange,
  onCustomNuChange,
  onNumMapsChange,
}) {
  return (
    <>
      <div className="panel-section">
        <h2 className="section-title">Neutrino Mass (mν)</h2>
        <div className="slider-group">
          <input
            type="range"
            className="slider"
            min="0"
            max="1.2"
            step="0.01"
            value={nuValue}
            onChange={onSliderChange}
          />
          <div className="slider-marks">
            {NU_VALUES.map(val => (
              <span 
                key={val}
                className={`mark ${Math.abs(nuValue - val) < 0.005 ? 'active' : ''}`}
                onClick={() => onSliderChange({ target: { value: val } })}
              >
                {val}
              </span>
            ))}
          </div>
        </div>
        <div className="slider-value">Current: {nuValue.toFixed(2)} eV</div>
        <div className="input-group">
          <label>Custom value (eV) - Step: 0.01</label>
          <input
            type="number"
            className={`input-field ${massError ? 'input-error' : ''}`}
            value={customNuValue}
            onChange={onCustomNuChange}
            step="0.01"
            min={MASS_LIMITS.min}
            max={MASS_LIMITS.max}
          />
          {massError && <span className="error-text">{massError}</span>}
        </div>
      </div>

      <div className="panel-section">
        <h2 className="section-title">Number of Maps</h2>
        <select
          className="select-field"
          value={numMaps}
          onChange={(e) => onNumMapsChange(parseInt(e.target.value))}
        >
          {NUM_MAPS_OPTIONS.map(num => (
            <option key={num} value={num}>{num}</option>
          ))}
        </select>
      </div>
    </>
  );
}

export default SingleModeControls;
