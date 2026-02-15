/**
 * Empty State component - Shown when no results
 */
import React from 'react';

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">🌌</div>
      <h3>No maps generated yet</h3>
      <p>Load the model and configure parameters to generate cosmic density maps</p>
    </div>
  );
}

export default EmptyState;
