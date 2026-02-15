/**
 * Client-side colormap application utilities
 * Allows instant colormap switching without API calls
 */

// Colormap definitions - each is an array of [r, g, b] values from 0-255
// These match matplotlib colormaps

export const COLORMAP_DATA = {
  // AFM Hot - black to red to yellow to white
  afm: generateAFMHot(),
  
  // Jet - blue to cyan to yellow to red
  jet: generateJet(),
  
  // Viridis - purple to green to yellow
  viridis: generateViridis(),
  
  // Ocean - green to blue
  ocean: generateOcean(),
  
  // Hot - black to red to yellow to white
  hot: generateHot(),
};

function generateAFMHot() {
  const colors = [];
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    // AFM hot: black -> red -> yellow -> white
    const r = Math.min(255, Math.floor(t < 0.5 ? t * 2 * 255 : 255));
    const g = Math.min(255, Math.floor(t < 0.5 ? 0 : (t - 0.5) * 2 * 255));
    const b = Math.min(255, Math.floor(t < 0.75 ? 0 : (t - 0.75) * 4 * 255));
    colors.push([r, g, b]);
  }
  return colors;
}

function generateJet() {
  const colors = [];
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    let r, g, b;
    
    if (t < 0.125) {
      r = 0;
      g = 0;
      b = Math.floor(128 + t * 8 * 127);
    } else if (t < 0.375) {
      r = 0;
      g = Math.floor((t - 0.125) * 4 * 255);
      b = 255;
    } else if (t < 0.625) {
      r = Math.floor((t - 0.375) * 4 * 255);
      g = 255;
      b = Math.floor(255 - (t - 0.375) * 4 * 255);
    } else if (t < 0.875) {
      r = 255;
      g = Math.floor(255 - (t - 0.625) * 4 * 255);
      b = 0;
    } else {
      r = Math.floor(255 - (t - 0.875) * 4 * 127);
      g = 0;
      b = 0;
    }
    
    colors.push([Math.min(255, Math.max(0, r)), Math.min(255, Math.max(0, g)), Math.min(255, Math.max(0, b))]);
  }
  return colors;
}

function generateViridis() {
  // Viridis colormap data (sampled)
  const viridisData = [
    [68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142],
    [38, 130, 142], [31, 158, 137], [53, 183, 121], [109, 205, 89],
    [180, 222, 44], [253, 231, 37]
  ];
  return interpolateColormap(viridisData);
}

function generateOcean() {
  const colors = [];
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    // Ocean: green -> blue -> dark blue
    const r = Math.floor(t < 0.5 ? 0 : (t - 0.5) * 2 * 128);
    const g = Math.floor(t < 0.5 ? 128 * (1 - t * 2) : 0);
    const b = Math.floor(t < 0.5 ? 128 + t * 2 * 127 : 255 - (t - 0.5) * 2 * 127);
    colors.push([r, g, b]);
  }
  return colors;
}

function generateHot() {
  const colors = [];
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    // Hot: black -> red -> yellow -> white
    const r = Math.min(255, Math.floor(t * 3 * 255));
    const g = Math.min(255, Math.floor(t < 0.33 ? 0 : (t - 0.33) * 3 * 255));
    const b = Math.min(255, Math.floor(t < 0.67 ? 0 : (t - 0.67) * 3 * 255));
    colors.push([r, g, b]);
  }
  return colors;
}

function interpolateColormap(keyColors) {
  const colors = [];
  const segments = keyColors.length - 1;
  
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    const segmentIndex = Math.min(segments - 1, Math.floor(t * segments));
    const segmentT = (t * segments) - segmentIndex;
    
    const c1 = keyColors[segmentIndex];
    const c2 = keyColors[segmentIndex + 1];
    
    colors.push([
      Math.floor(c1[0] + (c2[0] - c1[0]) * segmentT),
      Math.floor(c1[1] + (c2[1] - c1[1]) * segmentT),
      Math.floor(c1[2] + (c2[2] - c1[2]) * segmentT)
    ]);
  }
  
  return colors;
}

/**
 * Apply colormap to grayscale image data
 * @param {string} grayscaleDataUrl - Base64 grayscale image
 * @param {string} colormapName - Name of colormap to apply
 * @returns {Promise<string>} - Base64 colored image
 */
export async function applyColormap(grayscaleDataUrl, colormapName) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      
      // Draw grayscale image
      ctx.drawImage(img, 0, 0);
      
      // Get pixel data
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      // Get colormap
      const colormap = COLORMAP_DATA[colormapName] || COLORMAP_DATA.viridis;
      
      // Apply colormap
      for (let i = 0; i < data.length; i += 4) {
        // Use red channel as grayscale value (assuming grayscale image)
        const grayValue = data[i];
        const color = colormap[grayValue];
        
        data[i] = color[0];     // R
        data[i + 1] = color[1]; // G
        data[i + 2] = color[2]; // B
        // Alpha stays the same
      }
      
      // Put modified data back
      ctx.putImageData(imageData, 0, 0);
      
      // Convert to data URL
      resolve(canvas.toDataURL('image/png'));
    };
    
    img.onerror = reject;
    img.src = grayscaleDataUrl;
  });
}

/**
 * Apply colormap to all images in an array
 * @param {Array} images - Array of image objects with grayscale property
 * @param {string} colormapName - Name of colormap to apply
 * @returns {Promise<Array>} - Array of images with colored image property
 */
export async function applyColormapToImages(images, colormapName) {
  return Promise.all(
    images.map(async (img) => ({
      ...img,
      image: await applyColormap(img.grayscale, colormapName)
    }))
  );
}
