/**
 * Main Application Component
 * Orchestrates the nuGAN web interface
 */
import React, { useState, useCallback } from 'react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

// Hooks
import { useModelLoader, useGeneration, useColormap } from './hooks';

// Components
import Header from './components/Header';
import Footer from './components/Footer';
import ImageViewer from './components/ImageViewer';
import {
  ModelLoader,
  ModeToggle,
  SingleModeControls,
  GridModeControls,
  GenerateButton,
} from './components/ControlPanel';
import {
  OutputHeader,
  SingleModeResults,
  GridModeResults,
  EmptyState,
  LoadingState,
} from './components/OutputPanel';

// Config
import { DEFAULTS, MASS_LIMITS, NU_VALUES, MAX_MASSES } from './config';

import './App.css';

function App() {
  // Custom hooks for logic
  const {
    modelLoaded,
    isLoading,
    isCheckingModel,
    modelLoadTime,
    error: modelError,
    setError: setModelError,
    handleLoadModel,
  } = useModelLoader();

  const {
    isGenerating,
    generateTime,
    usedSeed,
    generatedImages,
    setGeneratedImages,
    rawImages,
    gridData,
    setGridData,
    rawGridData,
    error: genError,
    setError: setGenError,
    handleGenerate,
    handleCancelGeneration,
  } = useGeneration();

  // Generation parameters
  const [nuValue, setNuValue] = useState(DEFAULTS.nuValue);
  const [customNuValue, setCustomNuValue] = useState(DEFAULTS.nuValue.toFixed(2));
  const [numMaps, setNumMaps] = useState(DEFAULTS.numMaps);
  const [colormap, setColormap] = useState(DEFAULTS.colormap);
  
  // Grid mode parameters
  const [gridMode, setGridMode] = useState(false);
  const [selectedMasses, setSelectedMasses] = useState(DEFAULTS.selectedMasses);
  const [customGridMass, setCustomGridMass] = useState('');
  const [numRows, setNumRows] = useState(DEFAULTS.numRows);
  
  // Validation errors
  const [massError, setMassError] = useState(null);
  const [gridMassError, setGridMassError] = useState(null);
  
  // Image viewer
  const [selectedImage, setSelectedImage] = useState(null);

  // Colormap hook
  const { isApplyingColormap } = useColormap({
    colormap,
    gridMode,
    rawImages,
    rawGridData,
    setGeneratedImages,
    setGridData,
  });

  // Combined error
  const error = modelError || genError;

  // Event handlers
  const handleSliderChange = useCallback((e) => {
    const value = parseFloat(e.target.value);
    setNuValue(value);
    setCustomNuValue(value.toFixed(2));
    setMassError(null);
  }, []);

  const handleCustomNuChange = useCallback((e) => {
    const value = e.target.value;
    setCustomNuValue(value);
    setMassError(null);
    const parsed = parseFloat(value);
    if (!isNaN(parsed)) {
      if (parsed > MASS_LIMITS.max) {
        setMassError(`Mass cannot exceed ${MASS_LIMITS.max} eV`);
      } else if (parsed < MASS_LIMITS.min) {
        setMassError('Mass cannot be negative');
      } else {
        setNuValue(parsed);
      }
    }
  }, []);

  const toggleMassSelection = useCallback((mass) => {
    setSelectedMasses(prev => {
      if (prev.includes(mass)) {
        return prev.filter(m => m !== mass);
      } else {
        if (prev.length >= MAX_MASSES) {
          setGridMassError(`Maximum ${MAX_MASSES} masses allowed`);
          return prev;
        }
        setGridMassError(null);
        return [...prev, mass].sort((a, b) => a - b);
      }
    });
  }, []);

  const handleAddCustomMass = useCallback(() => {
    const parsed = parseFloat(customGridMass);
    if (isNaN(parsed)) {
      setGridMassError('Please enter a valid number');
      return;
    }
    if (parsed > MASS_LIMITS.max) {
      setGridMassError(`Mass cannot exceed ${MASS_LIMITS.max} eV`);
      return;
    }
    if (parsed < MASS_LIMITS.min) {
      setGridMassError('Mass cannot be negative');
      return;
    }
    if (selectedMasses.includes(parsed)) {
      setGridMassError('Mass already added');
      return;
    }
    if (selectedMasses.length >= MAX_MASSES) {
      setGridMassError(`Maximum ${MAX_MASSES} masses allowed`);
      return;
    }
    setGridMassError(null);
    setSelectedMasses(prev => [...prev, parsed].sort((a, b) => a - b));
    setCustomGridMass('');
  }, [customGridMass, selectedMasses]);

  const handleRemoveCustomMass = useCallback((mass) => {
    if (!NU_VALUES.includes(mass)) {
      setSelectedMasses(prev => prev.filter(m => m !== mass));
    }
  }, []);

  const onGenerate = useCallback(() => {
    handleGenerate({
      modelLoaded,
      gridMode,
      selectedMasses,
      numRows,
      colormap,
      nuValue,
      numMaps,
    });
  }, [handleGenerate, modelLoaded, gridMode, selectedMasses, numRows, colormap, nuValue, numMaps]);

  const handleDownloadAll = useCallback(async () => {
    const zip = new JSZip();
    
    if (!gridMode && generatedImages.length > 0) {
      const folder = zip.folder(`nuGAN_mv${nuValue.toFixed(2)}eV`);
      for (let i = 0; i < generatedImages.length; i++) {
        const img = generatedImages[i];
        const base64Data = img.image.split(',')[1];
        // Add seed to filename
        const filename = `mv${nuValue.toFixed(2)}eV_sample${String(i + 1).padStart(3, '0')}_seed${img.seed || usedSeed}.png`;
        folder.file(filename, base64Data, { base64: true });
      }
      const content = await zip.generateAsync({ type: 'blob' });
      saveAs(content, `nuGAN_mv${nuValue.toFixed(2)}eV.zip`);
    } else if (gridMode && gridData) {
      const folder = zip.folder(`nuGAN_grid`);
      for (let rowIdx = 0; rowIdx < gridData.grid.length; rowIdx++) {
        const row = gridData.grid[rowIdx];
        for (let j = 0; j < row.maps.length; j++) {
          const cell = row.maps[j];
          const base64Data = cell.image.split(',')[1];
          // Add seed to filename
          const filename = `mv${cell.nu_value.toFixed(2)}eV_sample${String(rowIdx + 1).padStart(3, '0')}_seed${row.seed}.png`;
          folder.file(filename, base64Data, { base64: true });
        }
      }
      const content = await zip.generateAsync({ type: 'blob' });
      saveAs(content, `nuGAN_grid.zip`);
    }
  }, [gridMode, generatedImages, gridData, nuValue]);

  // Image navigation handlers
  const handlePrevImage = useCallback(() => {
    if (!gridMode && generatedImages.length > 0) {
      const currentIdx = selectedImage.index;
      if (currentIdx > 0) {
        const prevImg = generatedImages[currentIdx - 1];
        setSelectedImage({ ...prevImg, index: currentIdx - 1, nuValue, seed: usedSeed });
      }
    } else if (gridMode && gridData) {
      const currentSampleNum = selectedImage.sampleNumber;
      const currentNuValue = selectedImage.nuValue;
      if (currentSampleNum > 1) {
        const prevRowIdx = currentSampleNum - 2;
        const colIdx = gridData.nu_values.indexOf(currentNuValue);
        const row = gridData.grid[prevRowIdx];
        const cell = row.maps[colIdx];
        setSelectedImage({
          ...cell,
          index: prevRowIdx * gridData.nu_values.length + colIdx,
          sampleNumber: prevRowIdx + 1,
          nuValue: cell.nu_value,
          seed: row.seed
        });
      }
    }
  }, [gridMode, generatedImages, gridData, selectedImage, nuValue, usedSeed]);

  const handleNextImage = useCallback(() => {
    if (!gridMode && generatedImages.length > 0) {
      const currentIdx = selectedImage.index;
      if (currentIdx < generatedImages.length - 1) {
        const nextImg = generatedImages[currentIdx + 1];
        setSelectedImage({ ...nextImg, index: currentIdx + 1, nuValue, seed: usedSeed });
      }
    } else if (gridMode && gridData) {
      const currentSampleNum = selectedImage.sampleNumber;
      const currentNuValue = selectedImage.nuValue;
      if (currentSampleNum < gridData.grid.length) {
        const nextRowIdx = currentSampleNum;
        const colIdx = gridData.nu_values.indexOf(currentNuValue);
        const row = gridData.grid[nextRowIdx];
        const cell = row.maps[colIdx];
        setSelectedImage({
          ...cell,
          index: nextRowIdx * gridData.nu_values.length + colIdx,
          sampleNumber: nextRowIdx + 1,
          nuValue: cell.nu_value,
          seed: row.seed
        });
      }
    }
  }, [gridMode, generatedImages, gridData, selectedImage, nuValue, usedSeed]);

  const hasPrev = !gridMode 
    ? selectedImage?.index > 0
    : gridMode && gridData && selectedImage?.sampleNumber > 1;

  const hasNext = !gridMode 
    ? selectedImage?.index < generatedImages.length - 1
    : gridMode && gridData && selectedImage?.sampleNumber < gridData?.grid?.length;

  const hasResults = generatedImages.length > 0 || gridData;
  const showEmptyState = !isGenerating && !isCheckingModel && !hasResults;

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        <aside className="control-panel">
          <ModelLoader
            modelLoaded={modelLoaded}
            isLoading={isLoading}
            modelLoadTime={modelLoadTime}
            onLoadModel={handleLoadModel}
          />

          <ModeToggle
            gridMode={gridMode}
            onModeChange={setGridMode}
          />

          {!gridMode ? (
            <SingleModeControls
              nuValue={nuValue}
              customNuValue={customNuValue}
              numMaps={numMaps}
              massError={massError}
              onSliderChange={handleSliderChange}
              onCustomNuChange={handleCustomNuChange}
              onNumMapsChange={setNumMaps}
            />
          ) : (
            <GridModeControls
              selectedMasses={selectedMasses}
              customGridMass={customGridMass}
              numRows={numRows}
              gridMassError={gridMassError}
              onToggleMass={toggleMassSelection}
              onCustomMassChange={setCustomGridMass}
              onAddCustomMass={handleAddCustomMass}
              onRemoveCustomMass={handleRemoveCustomMass}
              onNumRowsChange={setNumRows}
            />
          )}

          <GenerateButton
            modelLoaded={modelLoaded}
            isGenerating={isGenerating}
            isCheckingModel={isCheckingModel}
            onGenerate={onGenerate}
            onCancel={handleCancelGeneration}
          />
        </aside>

        <section className="output-panel">
          <div className="output-panel-content">
            <OutputHeader
              colormap={colormap}
              isApplyingColormap={isApplyingColormap}
              hasResults={hasResults}
              onColormapChange={setColormap}
              onDownloadAll={handleDownloadAll}
            />

            {error && <div className="error-banner">{error}</div>}

            {isCheckingModel && (
              <LoadingState message="Checking server status..." />
            )}

            {isGenerating && (
              <LoadingState 
                message={`Generating ${gridMode ? `${selectedMasses.length * numRows}` : numMaps} density maps...`}
                hint="This may take a moment for large batches"
              />
            )}

            {!gridMode && (
              <SingleModeResults
                generatedImages={generatedImages}
                nuValue={nuValue}
                colormap={colormap}
                usedSeed={usedSeed}
                generateTime={generateTime}
                onImageClick={setSelectedImage}
              />
            )}

            {gridMode && (
              <GridModeResults
                gridData={gridData}
                generateTime={generateTime}
                onImageClick={setSelectedImage}
              />
            )}

            {showEmptyState && <EmptyState />}
          </div>
        </section>
      </main>

      <Footer />

      {selectedImage && (
        <ImageViewer 
          image={selectedImage} 
          onClose={() => setSelectedImage(null)}
          currentIndex={!gridMode ? selectedImage.index : (selectedImage.sampleNumber - 1)}
          totalCount={!gridMode ? generatedImages.length : gridData?.grid?.length || 0}
          onPrev={handlePrevImage}
          onNext={handleNextImage}
          hasPrev={hasPrev}
          hasNext={hasNext}
        />
      )}
    </div>
  );
}

export default App;
