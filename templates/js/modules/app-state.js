/**
 * app-state.js
 * Manages shared application state across modules
 */

// Create namespace for shared state
const AppState = (function() {
  // Create socket connection
  const socket = io();
  
  // Application state variables
  let isDetecting = false;
  let isPomodoroActive = false;
  let currentTimerMode = "pomodoro";
  
  // Chart instances for later reference
  let focusChartInstance = null;
  let distributionChartInstance = null;
  let pointTrendChart = null;
  
  // Timer reference
  let detectionLoadingTimeout = null;
  
  return {
    isStoppingDetection: false,
    setStoppingDetection: (value) => { isStoppingDetection = value; },
    // Getters
    getSocket: () => socket,
    isDetecting: () => isDetecting,
    isPomodoroActive: () => isPomodoroActive,
    getCurrentTimerMode: () => currentTimerMode,
    getCharts: () => ({
      focusChart: focusChartInstance,
      distributionChart: distributionChartInstance,
      pointTrendChart: pointTrendChart
    }),
    getDetectionLoadingTimeout: () => detectionLoadingTimeout,
    
    // Setters
    setDetecting: (value) => { isDetecting = value; },
    setPomodoroActive: (value) => { isPomodoroActive = value; },
    setCurrentTimerMode: (value) => { currentTimerMode = value; },
    setFocusChart: (chart) => { focusChartInstance = chart; },
    setDistributionChart: (chart) => { distributionChartInstance = chart; },
    setPointTrendChart: (chart) => { pointTrendChart = chart; },
    setDetectionLoadingTimeout: (timeout) => { detectionLoadingTimeout = timeout; },
    
    // Clear timeout helper
    clearDetectionLoadingTimeout: () => {
      if (detectionLoadingTimeout) {
        clearTimeout(detectionLoadingTimeout);
        detectionLoadingTimeout = null;
      }
    }
  };
})();

// Export the AppState namespace
window.AppState = AppState;