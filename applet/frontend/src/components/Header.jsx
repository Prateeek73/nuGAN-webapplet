/**
 * Header component
 */
import React from 'react';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1>νGAN</h1>
        <p className="subtitle">Neutrino Mass Cosmic Density Map Generator</p>
        <p className="description">
          Deep learning emulator for cosmic web simulations with massive neutrinos
        </p>
      </div>
    </header>
  );
}

export default Header;
