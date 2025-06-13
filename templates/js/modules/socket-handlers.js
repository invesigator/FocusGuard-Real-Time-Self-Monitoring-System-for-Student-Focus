// Update socket-handlers.js to ensure proper data loading
const SocketHandlers = (function() {
  // Initialize socket event handlers
  function initialize() {
    const socket = AppState.getSocket();
    
    // Add connect handler to load data immediately on connection
    socket.on('connect', () => {
      console.log('Socket connected - requesting initial data');
      
      // Request gamification data as soon as connected
      socket.emit('get_gamification_status');
      socket.emit('check_daily_status');
      
      // Also request other necessary data
      socket.emit('get_timer_status');
      socket.emit('get_current_settings');
      
      // Check if we have saved statistics in sessionStorage
      // If we're not actively detecting, load from sessionStorage instead
      if (!AppState.isDetecting() && typeof Statistics !== 'undefined') {
        const hasSavedStats = checkForSavedStats();
        
        if (hasSavedStats) {
          // Load saved stats from sessionStorage
          try {
            const savedData = JSON.parse(sessionStorage.getItem('lastVisualizationData'));
            console.log('Loading visualization data from sessionStorage on connect');
            Statistics.handleVisualizationData(savedData);
          } catch (e) {
            console.error('Error loading visualization data on connect:', e);
            Statistics.requestVisualizationData();
          }
        } else {
          // If no saved stats, load empty state
          Statistics.requestVisualizationData();
        }
      }
    });
    
    // Detection status events
    socket.on("detection_status", (data) => {
      console.log("Detection status update:", data);
      Detection.handleDetectionStatus(data);
    });
    
    // Pomodoro timer events
    socket.on("pomodoro_update", Pomodoro.handleTimerUpdate);
    
    // Statistics events
    socket.on("statistics_update", Statistics.handleStatisticsUpdate);
    
    // Alert events with sound notifications
    socket.on("drowsy_event", () => {
      console.log("Drowsy event detected!");
      Notifications.playNotificationSound("drowsy");
    });
    
    socket.on("yawn_event", () => {
      console.log("Yawn event detected!");
      Notifications.playNotificationSound("yawn");
    });
    
    socket.on("distraction_event", () => {
      console.log("Distraction event detected!");
      Notifications.playNotificationSound("distraction");
    });
    
    // Enhanced Visualization data event handler
    socket.on("visualization_data", (data) => {
      console.log("Visualization data received:", data ? Object.keys(data) : 'empty');
      
      // If data is valid, save it to sessionStorage for persistence across refreshes
      if (data && Object.keys(data).length > 0) {
        try {
          // Only save to sessionStorage if we're not in active detection mode
          // or if we just ended a session (marked by the 'justEndedSession' flag)
          if (!AppState.isDetecting() || window.justEndedSession) {
            sessionStorage.setItem('lastVisualizationData', JSON.stringify(data));
            console.log('Visualization data saved to sessionStorage');
            
            // Reset the flag if it was set
            if (window.justEndedSession) {
              window.justEndedSession = false;
            }
          }
        } catch (e) {
          console.error('Error saving to sessionStorage:', e);
        }
      }
      
      // Call the original handler
      if (typeof Statistics !== 'undefined' && Statistics.handleVisualizationData) {
        Statistics.handleVisualizationData(data);
      }
    });
    
    // Settings events
    socket.on("settings_updated", Settings.handleSettingsUpdate);
    socket.on("current_settings", Settings.updateUIFromSettings);
    
    // Gamification events with improved logging and error handling
    socket.on('gamification_update', (data) => {
      console.log('Received gamification update:', data);
      
      if (data.error) {
        console.error("Error in gamification data:", data.error);
        return;
      }
      
      // Check if data has the expected structure
      if (!data.level && !data.points) {
        console.warn("Gamification data missing essential fields:", data);
      }
      
      // Update the UI with available data
      Gamification.updateGamificationUI(data);
      
      // Ensure check-in button is visible after data update
      setTimeout(() => {
        Gamification.ensureCheckInButtonVisible();
      }, 100);
    });
    
    socket.on('login_streak_update', Gamification.handleLoginStreakUpdate);
    
    socket.on('daily_check_in_response', (data) => {
      console.log('Daily check-in response:', data);
      Gamification.handleDailyCheckInResponse(data);
      
      // Request updated status after check-in
      socket.emit('get_gamification_status');
    });
    
    socket.on('daily_status_check', (data) => {
      console.log('Daily status check:', data);
      Gamification.handleDailyStatusCheck(data);
      
      // Ensure button is visible after status check
      setTimeout(() => {
        Gamification.ensureCheckInButtonVisible();
      }, 100);
    });
    
    socket.on('leaderboard_data', (data) => {
      if (data.error) {
        console.error("Error updating leaderboard:", data.error);
        return;
      }
      
      // Reset to first page when new data is received
      if (typeof Gamification.resetLeaderboardPage === 'function') {
        Gamification.resetLeaderboardPage();
      }
      
      Gamification.updateLeaderboard(data.users);
    });
    
    // Analytics events
    socket.on('analytics_data', Statistics.updateAnalyticsDisplay);
    
    socket.on('analytics_export_ready', (data) => {
      if (data.error || data.status === 'error') {
        Notifications.showNotification(`Error exporting analytics: ${data.message || data.error}`, 'error');
        return;
      }
      
      Notifications.showNotification('Analytics data exported successfully', 'success');
    });
    
    // New handler for gamification data save confirmation
    socket.on('gamification_save_status', (data) => {
      console.log('Gamification save status:', data);
      if (data.success) {
        console.log('Gamification data saved successfully');
      } else {
        console.error('Failed to save gamification data:', data.error);
      }
    });

    // Add new session_history_data event handler
    socket.on('session_history_data', (data) => {
      console.log('Received session history data:', data);
      
      if (data.error) {
          console.error('Error loading session history:', data.error);
          // Show empty state
          Statistics.updateHistoricalSessions([]);
          return;
      }
      
      // DON'T reset to first page when new data is received - REMOVE THIS LINE
      // if (typeof Statistics.resetPage === 'function') {
      //     Statistics.resetPage();
      // }
      
      // Instead, preserve the current page position
      // Pass all sessions to the function that handles pagination internally
      Statistics.updateHistoricalSessions(data.sessions || []);
    });
    
    // Setup logout handler to clear sessionStorage
    setupLogoutHandler();
    
    // Setup statistics tab handler
    setupStatisticsTabHandler();
    
    // Setup page unload event to stop detection if active
    setupPageUnloadHandler();
    
    console.log("Socket handlers initialized with enhanced error handling");
  }
  
  // Helper function to check for saved stats
  function checkForSavedStats() {
    try {
      const savedData = sessionStorage.getItem('lastVisualizationData');
      return savedData && savedData !== 'null' && savedData !== 'undefined';
    } catch (e) {
      console.error('Error checking sessionStorage:', e);
      return false;
    }
  }
  

  // Set up logout handler to clear sessionStorage
  function setupLogoutHandler() {
    // Find all logout links on the page
    const logoutLinks = document.querySelectorAll('a[href="/logout"]');
    
    logoutLinks.forEach(link => {
      link.addEventListener('click', () => {
        console.log('Logout detected, clearing sessionStorage and localStorage tab data');
        try {
          // Clear visualization data from sessionStorage
          sessionStorage.removeItem('lastVisualizationData');
          
          // Clear active tab information from localStorage
          localStorage.removeItem('focusguard_active_tab');
        } catch (e) {
          console.error('Error clearing storage data:', e);
        }
      });
    });
  }
  
  // Set up tab handler for statistics
  function setupStatisticsTabHandler() {
    const statisticsTab = document.getElementById('tab-statistics');
    if (statisticsTab) {
        statisticsTab.addEventListener('click', () => {
            console.log('Statistics tab clicked');
            
            // Request visualization data
            if (!AppState.isDetecting()) {
                const hasSavedStats = checkForSavedStats();
                
                if (hasSavedStats) {
                    try {
                        // Get saved data from sessionStorage
                        const savedData = JSON.parse(sessionStorage.getItem('lastVisualizationData'));
                        console.log('Loading visualization data from sessionStorage');
                        
                        // Use it to update the UI directly
                        if (typeof Statistics !== 'undefined' && Statistics.handleVisualizationData) {
                            Statistics.handleVisualizationData(savedData);
                        }
                    } catch (e) {
                        console.error('Error loading from sessionStorage:', e);
                        // If there's an error, request fresh data
                        AppState.getSocket().emit('get_visualization_data');
                    }
                } else {
                    // If no saved data, show empty state
                    if (typeof Statistics !== 'undefined' && Statistics.requestVisualizationData) {
                        Statistics.requestVisualizationData();
                    }
                }
            } else {
                // If actively detecting, request current data
                AppState.getSocket().emit('get_visualization_data');
            }
            
            // Also request session history data (new)
            AppState.getSocket().emit('get_session_history');
        });
    }
  }
  
  /**
   * Ensures detection is stopped when page is unloaded
   * Uses multiple methods to maximize the chance of successful shutdown
   */
  function setupPageUnloadHandler() {
    // Flag to prevent duplicate stop requests
    let unloadStopSent = false;
    
    window.addEventListener('beforeunload', function() {
      if (AppState.isDetecting() && !unloadStopSent) {
        unloadStopSent = true;
        
        // 1. First attempt: Use socket event
        const socket = AppState.getSocket();
        if (socket) {
          socket.emit('stop_detection');
        }
        
        // 2. Second attempt: Use a synchronous XHR as backup
        try {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', '/api/stop_detection_emergency', false); // Synchronous request
          xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
          xhr.send(JSON.stringify({ emergency: true }));
          
          console.log('Emergency detection stop triggered on page unload');
        } catch (e) {
          console.error('Failed to perform emergency detection stop:', e);
        }
        
        // 3. Third attempt: Set a flag in localStorage to check on page reload
        try {
          localStorage.setItem('focusguard_detection_active', 'true');
          localStorage.setItem('focusguard_detection_timestamp', Date.now());
        } catch (e) {
          console.error('Failed to set detection flag in localStorage:', e);
        }
      }
    });
    
    // Add a pagehide listener as additional backup
    window.addEventListener('pagehide', function() {
      if (AppState.isDetecting() && !unloadStopSent) {
        unloadStopSent = true;
        
        // Try to use the emergency endpoint
        try {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', '/api/stop_detection_emergency', false);
          xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
          xhr.send(JSON.stringify({ emergency: true }));
        } catch (e) {
          console.error('Failed to perform emergency detection stop:', e);
        }
      }
    });
    
    // Check on page load if detection was active during last unload
    window.addEventListener('load', function() {
      try {
        const wasActive = localStorage.getItem('focusguard_detection_active');
        const timestamp = localStorage.getItem('focusguard_detection_timestamp');
        
        if (wasActive === 'true' && timestamp) {
          // Only act if this happened recently (within last 10 seconds)
          const elapsed = Date.now() - parseInt(timestamp);
          if (elapsed < 10000) {
            // Send an emergency stop request just in case
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/stop_detection_emergency', true);
            xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
            xhr.send(JSON.stringify({ emergency: true }));
            
            console.log('Sent emergency stop after page reload');
          }
          
          // Clear the flag
          localStorage.removeItem('focusguard_detection_active');
          localStorage.removeItem('focusguard_detection_timestamp');
        }
      } catch (e) {
        console.error('Error checking detection status after reload:', e);
      }
    });
  }
  
  // Listen for session end events (dispatched from Detection.js)
  document.addEventListener('sessionEnded', function(e) {
    console.log('Session ended event detected in socket handlers');
    
    // Set flag to indicate we should save the next visualization data
    window.justEndedSession = true;
    
    // Request the final visualization data
    const socket = AppState.getSocket();
    if (socket) {
      socket.emit('get_visualization_data');
    }
  });

  // Public methods
  return {
    initialize: initialize,
    checkForSavedStats: checkForSavedStats
  };
})();

// Export the SocketHandlers namespace
window.SocketHandlers = SocketHandlers;