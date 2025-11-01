/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// Backend API base URL - Updated for simplified backend
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// API Endpoints - Updated for simplified LLVM optimization backend
export const API_ENDPOINTS = {
  // Core LLVM Optimization Endpoints
  features: `${API_BASE_URL}/api/llvm/features`,
  optimize: `${API_BASE_URL}/api/llvm/optimize`,
  standard: `${API_BASE_URL}/api/llvm/standard`,
  compare: `${API_BASE_URL}/api/llvm/compare`,
  health: `${API_BASE_URL}/api/llvm/health`,
  
  // Legacy endpoints (for backward compatibility - will redirect to new endpoints)
  compareFile: `${API_BASE_URL}/api/llvm/compare`,
  compareQuick: `${API_BASE_URL}/api/llvm/compare`,
  
  // Analytics (if needed, can be added later)
  analyticsModels: `${API_BASE_URL}/api/analytics/models`,
  analyticsFeatures: `${API_BASE_URL}/api/analytics/features`,
  analyticsPasses: `${API_BASE_URL}/api/analytics/passes`,
  analyticsSystem: `${API_BASE_URL}/api/analytics/system`,
  
  // Utility
  status: `${API_BASE_URL}/api/llvm/health`,
  info: `${API_BASE_URL}/`,
  validateSource: `${API_BASE_URL}/api/llvm/features`, // Can validate by extracting features
};

export default API_ENDPOINTS;
