/**
 * Generate Button component
 */
import React from 'react';

function GenerateButton({
  modelLoaded,
  isGenerating,
  isCheckingModel,
  onGenerate,
  onCancel,
}) {
  return (
    <div className="panel-section">
      {!isGenerating ? (
        <button
          className="btn btn-generate"
          onClick={onGenerate}
          disabled={!modelLoaded || isGenerating || isCheckingModel}
        >
          Generate Maps
        </button>
      ) : (
        <button
          className="btn btn-cancel"
          onClick={onCancel}
        >
          ✕ Cancel Generation
        </button>
      )}
    </div>
  );
}

export default GenerateButton;
