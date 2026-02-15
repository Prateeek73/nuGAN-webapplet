import React, { useEffect, useCallback } from 'react';

function ImageViewer({ image, onClose, onPrev, onNext, hasPrev, hasNext, currentIndex, totalCount }) {
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'ArrowLeft' && hasPrev) onPrev();
    if (e.key === 'ArrowRight' && hasNext) onNext();
  }, [onClose, onPrev, onNext, hasPrev, hasNext]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [handleKeyDown]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!image) return null;

  return (
    <div 
      className="image-viewer-overlay" 
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-label="Image viewer"
    >
      {hasPrev && (
        <button 
          className="image-viewer-nav nav-prev" 
          onClick={onPrev}
          aria-label="Previous image"
        >
          ‹
        </button>
      )}
      <div className="image-viewer-container">
        <button className="image-viewer-close" onClick={onClose} aria-label="Close viewer">×</button>
        <div className="image-viewer-top-info">
          <span className="image-viewer-title">
            {image.sampleNumber ? `Sample ${image.sampleNumber}` : `Map #${image.index + 1}`}
          </span>
          {image.nuValue !== undefined && (
            <span className="image-viewer-mass">mν = {image.nuValue.toFixed(2)} eV</span>
          )}
          {image.seed && (
            <span className="image-viewer-seed">Seed: {image.seed}</span>
          )}
          {totalCount > 1 && (
            <span className="image-viewer-counter">{currentIndex + 1} of {totalCount}</span>
          )}
        </div>
        <img src={image.image} alt="Full view" className="image-viewer-img" />
        <div className="image-viewer-bottom-stats">
          <div className="cell-stat-row">
            <span>Min: {image.stats.min.toFixed(3)}</span>
            <span>Max: {image.stats.max.toFixed(3)}</span>
          </div>
          <div className="cell-stat-row">
            <span>Mean: {image.stats.mean.toFixed(3)}</span>
            <span>Std: {image.stats.std.toFixed(3)}</span>
          </div>
        </div>
        <div className="image-viewer-hints">
          <span>← → Navigate</span>
          <span>Esc Close</span>
        </div>
      </div>
      {hasNext && (
        <button 
          className="image-viewer-nav nav-next" 
          onClick={onNext}
          aria-label="Next image"
        >
          ›
        </button>
      )}
    </div>
  );
}

export default ImageViewer;
