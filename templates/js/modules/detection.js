/**
 * detection.js
 * Handles camera detection functionality
 */

const Detection = (function() {
  // Private methods
  function startDetection() {
    // Show loading animation
    document.getElementById("placeholderFeed").classList.add("hidden");
    document.getElementById("loadingFeed").classList.remove("hidden");
    
    // Clear existing visualization data when starting a new detection
    if (typeof Statistics !== 'undefined' && Statistics.clearVisualizationData) {
      Statistics.clearVisualizationData();
    }
    
    // Emit socket event to start detection
    AppState.getSocket().emit("start_detection");
    
    // Disable start button and enable stop button
    document.getElementById("startBtn").disabled = true;
    document.getElementById("stopBtn").disabled = false;
    
    // Add loading timeout - if camera feed doesn't appear in 10 seconds, show error
    const timeout = setTimeout(() => {
      if (document.getElementById("loadingFeed").classList.contains("hidden") === false) {
        Notifications.showNotification("Camera initialization is taking longer than expected. Please check your camera permissions.", "error");
      }
    }, 15000);
    
    // Store the timeout
    AppState.setDetectionLoadingTimeout(timeout);
  }
  
  function stopDetection() {
    // Flag to track stop request to avoid duplicate calls
    if (AppState.isStoppingDetection) {
      console.log("Detection stopping already in progress");
      return;
    }
    
    console.log("Stopping detection...");
    AppState.isStoppingDetection = true;
    
    // First try the socket event to stop detection normally
    AppState.getSocket().emit("stop_detection");
    
    // As a backup, also send an emergency stop request via HTTP
    // This ensures the camera is released even if socket connection fails
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/stop_detection_emergency', true); // Async request as a backup
      xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
      xhr.send(JSON.stringify({ emergency: true }));
    } catch (e) {
      console.error("Error sending emergency stop request:", e);
    }
    
    // Show a stopping indicator
    Notifications.showNotification("Stopping detection...", "info");
    
    // Reset the flag after some time
    setTimeout(() => {
      AppState.isStoppingDetection = false;
    }, 2000);
  }
  
  function updateCurrentDetectionUI(settings) {
    // Update EAR display
    const earValue = document.getElementById('currentEAR');
    const earIndicator = document.getElementById('earIndicator');
    
    if (earValue && earIndicator && settings.eye_threshold) {
      earValue.textContent = settings.eye_threshold.toFixed(2);
      // Calculate width percentage (EAR range typically 0.1-0.3)
      const earPercent = (settings.eye_threshold / 0.3) * 100;
      earIndicator.style.width = `${Math.min(earPercent, 100)}%`;
    }
    
    // Update MAR display
    const marValue = document.getElementById('currentMAR');
    const marIndicator = document.getElementById('marIndicator');
    
    if (marValue && marIndicator && settings.mouth_threshold) {
      marValue.textContent = settings.mouth_threshold.toFixed(2);
      // Calculate width percentage (MAR range typically 0.5-2.0)
      const marPercent = (settings.mouth_threshold / 2.0) * 100;
      marIndicator.style.width = `${Math.min(marPercent, 100)}%`;
    }
    
    // Update Head Pose display
    const headPoseValue = document.getElementById('currentHeadPose');
    const headPoseIndicator = document.getElementById('headPoseIndicator');
    
    if (headPoseValue && headPoseIndicator && settings.head_pose_threshold) {
      headPoseValue.textContent = `${settings.head_pose_threshold.toFixed(0)}°`;
      // Calculate width percentage (Head Pose range typically 5-20 degrees)
      const headPosePercent = (settings.head_pose_threshold / 20) * 100;
      headPoseIndicator.style.width = `${Math.min(headPosePercent, 100)}%`;
    }
  }

  // Public methods
  return {
    setupButtons: function() {
      document.getElementById("startBtn").addEventListener("click", startDetection);
      document.getElementById("stopBtn").addEventListener("click", stopDetection);
    },
    
    handleDetectionStatus: function(data) {
      const isDetectingNow = data.status === "started";
      AppState.setDetecting(isDetectingNow);
      
      const statusIndicator = document.getElementById("statusIndicator");
      const statusText = document.getElementById("statusText");
      const videoFeed = document.getElementById("videoFeed");
      const placeholderFeed = document.getElementById("placeholderFeed");
      const loadingFeed = document.getElementById("loadingFeed");
    
      if (isDetectingNow) {
        // Clear the loading timeout
        AppState.clearDetectionLoadingTimeout();
        
        // Update status indicator
        statusIndicator.classList.remove("bg-red-500");
        statusIndicator.classList.add("bg-green-500");
        statusText.textContent = "Active";
        statusIndicator.innerHTML = '<i class="fas fa-circle-check mr-2"></i><span id="statusText">Active</span>';
    
        // Show video feed and hide placeholder and loading screens
        videoFeed.classList.remove("hidden");
        placeholderFeed.classList.add("hidden");
        loadingFeed.classList.add("hidden");
        videoFeed.src = "/video_feed";
    
        // Update button states
        document.getElementById("startBtn").disabled = true;
        document.getElementById("stopBtn").disabled = false;
        
        // Show a success notification
        Notifications.showNotification("Focus monitoring started successfully", "success");
      } else {
        // If there's an error message, show it
        if (data.status === "error" && data.message) {
          Notifications.showNotification(`Error: ${data.message}`, "error");
        }
        
        // Update status indicator
        statusIndicator.classList.remove("bg-green-500");
        statusIndicator.classList.add("bg-red-500");
        statusText.textContent = "Inactive";
        statusIndicator.innerHTML = '<i class="fas fa-circle-xmark mr-2"></i><span id="statusText">Inactive</span>';
    
        // Hide video feed and loading, show placeholder
        videoFeed.classList.add("hidden");
        loadingFeed.classList.add("hidden");
        placeholderFeed.classList.remove("hidden");
        videoFeed.src = "";
    
        // Update button states
        document.getElementById("startBtn").disabled = false;
        document.getElementById("stopBtn").disabled = true;
        
        // Process achievements if session was stopped
        if (data.status === 'stopped') {
          // If there are achievements or points, process them
          if (data.achievements || data.points) {
            Gamification.processSessionCompletion(data);
          }
          
          // Request latest visualization data to save it in sessionStorage
          // This ensures we capture the final statistics of the session
          // We use timeout to allow server to process the final data
          setTimeout(() => {
            // Request the final visualization data
            AppState.getSocket().emit("get_visualization_data");
            
            console.log("Requested final visualization data after session ended");
            
            // Add event to indicate session just ended, which statistics.js can detect
            document.dispatchEvent(new CustomEvent('sessionEnded', {
              detail: { timestamp: new Date().toISOString() }
            }));
          }, 500); // Small delay to ensure server has processed final data
        }
      }
    },
    
    updateDetectionUI: updateCurrentDetectionUI,
    
    // Expose stopDetection for navigation warning system
    stopDetection: stopDetection
  };
})();

// Export the Detection namespace
window.Detection = Detection;