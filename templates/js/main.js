/**
 * main.js
 * Main entry point for FocusGuard application
 */

// Main initialization function
document.addEventListener("DOMContentLoaded", () => {
  // Initialize UI components
  Tabs.initialize();
  Settings.setupRangeInputs();
  UIUtils.setupAlertStyles();
  
  // Initialize Pomodoro functionality
  Pomodoro.setupButtons();
  Pomodoro.setupModeButtons();
  Pomodoro.setupIconOnlyButtons();
  
  // Initialize settings
  Settings.setupButtons();
  
  // Initialize detection controls
  Detection.setupButtons();
  
  // Initialize gamification system
  Gamification.initialize();
  
  // Request initial data
  const socket = AppState.getSocket();
  socket.emit("get_timer_status");
  socket.emit("get_current_settings");
  
  // Set up socket event handlers
  SocketHandlers.initialize();
  
  // Initialize visualization refresh interval
  // Modify this to use a more intelligent refresh approach
  const visualizationRefreshInterval = 5000; // 5 seconds
  
  // Only refresh charts data, not session history, during auto-refresh
  const refreshCharts = () => {
    // Don't request session history in auto-refresh
    if (typeof AppState !== 'undefined' && AppState.isDetecting()) {
      socket.emit("get_visualization_data");
    }
    
    // Schedule next refresh
    setTimeout(refreshCharts, visualizationRefreshInterval);
  };
  
  // Start the refreshing cycle
  setTimeout(refreshCharts, visualizationRefreshInterval);
  
  // Request session history only when the statistics tab is first shown
  const statisticsTab = document.getElementById('tab-statistics');
  if (statisticsTab) {
    statisticsTab.addEventListener('click', () => {
      // Request session history data only when the tab is clicked
      socket.emit('get_session_history');
    });
  }
  
  // ADD NAVIGATION WARNING SYSTEM
  setupNavigationWarning();
  
  console.log("FocusGuard application initialized with improved refresh logic");
});

/**
 * Setup enhanced warning system for when users try to navigate away while detection is active
 * This fixes the issue with webcam staying on after refresh or navigation
 */
function setupNavigationWarning() {
  // Store a flag to prevent duplicate stop requests
  let stopRequestSent = false;
  
  // Add event listener for beforeunload event (page refresh or navigation)
  window.addEventListener('beforeunload', function(e) {
    if (AppState.isDetecting() && !stopRequestSent) {
      // Send emergency stop request
      try {
        stopRequestSent = true;
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/stop_detection_emergency', false); // Synchronous request
        xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
        xhr.send(JSON.stringify({ emergency: true }));
        console.log('Emergency detection stop triggered on page unload');
      } catch (e) {
        console.error('Failed to perform emergency detection stop:', e);
      }
      
      // Standard way to show a confirmation dialog before leaving page
      const confirmationMessage = 'Detection is still running. Are you sure you want to leave? Your session will be stopped.';
      e.returnValue = confirmationMessage;     // Standard for most browsers
      return confirmationMessage;              // For some older browsers
    }
  });
  
  // Use a more reliable method to catch all navigation attempts
  // This uses the History API to catch more navigation events
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;
  
  history.pushState = function() {
    checkNavigationWithDetection();
    return originalPushState.apply(this, arguments);
  };
  
  history.replaceState = function() {
    checkNavigationWithDetection();
    return originalReplaceState.apply(this, arguments);
  };
  
  // Helper function to check navigation when detection is active
  function checkNavigationWithDetection() {
    if (AppState.isDetecting() && !stopRequestSent) {
      const confirmed = confirm('Detection is still running. Are you sure you want to navigate? Your session will be stopped.');
      if (confirmed) {
        stopRequestSent = true;
        Detection.stopDetection();
      } else {
        // If user cancels, attempt to stay on current page
        setTimeout(() => {
          stopRequestSent = false;
        }, 500);
      }
    }
  }
  
  // Add a more comprehensive click handler for all links
  document.addEventListener('click', function(e) {
    // Find closest anchor tag (if any)
    const link = e.target.closest('a');
    
    if (link && AppState.isDetecting() && !stopRequestSent) {
      // Get the href attribute
      const href = link.getAttribute('href');
      
      // Only intercept links that navigate away from the page (not tab links or anchors)
      if (href && href !== '#' && !href.startsWith('#') && !link.classList.contains('tab-btn')) {
        e.preventDefault(); // Prevent the default link behavior
        
        // Show a confirmation dialog
        const confirmed = confirm('Detection is still running. Are you sure you want to leave? Your session will be stopped.');
        
        if (confirmed) {
          // Stop detection if user confirms
          stopRequestSent = true;
          Detection.stopDetection();
          
          // Give some time for detection to stop before navigating
          setTimeout(() => {
            window.location.href = href;
          }, 500);
        }
      }
    }
  });
  
  // Special handling for the refresh button (F5 or browser refresh button)
  // This uses the pageshow/pagehide events which are more reliable for detecting refreshes
  window.addEventListener('pagehide', function() {
    if (AppState.isDetecting() && !stopRequestSent) {
      stopRequestSent = true;
      // Use the emergency stop endpoint
      try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/stop_detection_emergency', false); // Synchronous request
        xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
        xhr.send(JSON.stringify({ emergency: true }));
        console.log('Emergency detection stop triggered on page hide');
      } catch (e) {
        console.error('Failed to perform emergency detection stop:', e);
      }
    }
  });
  
  // Add specific handling for the profile page link for more reliability
  const profileLinks = document.querySelectorAll('a[href="/profile"]');
  profileLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      if (AppState.isDetecting() && !stopRequestSent) {
        e.preventDefault();
        
        const confirmed = confirm('Detection is still running. Are you sure you want to go to profile page? Your session will be stopped.');
        
        if (confirmed) {
          // Stop detection if user confirms
          stopRequestSent = true;
          
          // First try the normal stopping mechanism
          if (typeof Detection !== 'undefined' && Detection.stopDetection) {
            Detection.stopDetection();
            
            // Wait longer to ensure detection stops completely
            setTimeout(() => {
              window.location.href = '/profile';
            }, 800);
          } else {
            // Emergency fallback if Detection module unavailable
            try {
              const xhr = new XMLHttpRequest();
              xhr.open('POST', '/api/stop_detection_emergency', false);
              xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
              xhr.send(JSON.stringify({ emergency: true }));
              
              setTimeout(() => {
                window.location.href = '/profile';
              }, 500);
            } catch (e) {
              console.error('Failed to perform emergency detection stop:', e);
              window.location.href = '/profile';
            }
          }
        }
      }
    });
  });
}