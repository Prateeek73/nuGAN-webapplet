/**
 * API Service Layer
 * Centralized API calls with error handling
 */
import axios from 'axios';
import { API_CONFIG } from '../config';

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_CONFIG.baseUrl,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Store for active request controllers (for cancellation)
const activeRequests = new Map();

/**
 * Create an AbortController for request cancellation
 */
export const createCancelToken = (key) => {
  // Cancel any existing request with the same key
  if (activeRequests.has(key)) {
    activeRequests.get(key).abort();
  }
  const controller = new AbortController();
  activeRequests.set(key, controller);
  return controller.signal;
};

/**
 * Cancel a specific request by key
 */
export const cancelRequest = (key) => {
  if (activeRequests.has(key)) {
    activeRequests.get(key).abort();
    activeRequests.delete(key);
  }
};

/**
 * Cancel all active requests
 */
export const cancelAllRequests = () => {
  activeRequests.forEach((controller) => controller.abort());
  activeRequests.clear();
};

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    console.error('[API] Response error:', message);
    return Promise.reject(new Error(message));
  }
);

/**
 * Health check
 */
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Load the nuGAN model
 */
export const loadModel = async (modelPath = null, signal = null) => {
  const response = await apiClient.post('/model/load', { model_path: modelPath }, { signal });
  return response.data;
};

/**
 * Get model status
 */
export const getModelStatus = async () => {
  const response = await apiClient.get('/model/status');
  return response.data;
};

/**
 * Generate density maps for a single mass value
 */
export const generateMaps = async ({ nuValue, numMaps, colormap, seed = null }, signal = null) => {
  const response = await apiClient.post('/generate', {
    nu_value: nuValue,
    num_maps: numMaps,
    colormap,
    seed,
  }, { signal });
  return response.data;
};

/**
 * Generate grid of density maps for multiple masses
 */
export const generateGrid = async ({ nuValues, numRows, colormap, baseSeed = null }, signal = null) => {
  const response = await apiClient.post('/generate/grid', {
    nu_values: nuValues,
    num_rows: numRows,
    colormap,
    base_seed: baseSeed,
  }, { signal });
  return response.data;
};

/**
 * Get available colormaps from server
 */
export const getColormaps = async () => {
  const response = await apiClient.get('/colormaps');
  return response.data;
};

export default apiClient;
