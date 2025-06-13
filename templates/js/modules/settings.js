/**
 * settings.js
 * Handles application settings functionality
 */

const Settings = (function() {
  // Private methods
  function setupRangeInputs() {
    document.querySelectorAll('input[type="range"]').forEach((range) => {
      const valueDisplay = document.getElementById(`${range.id}Value`);
      if (valueDisplay) {
        range.addEventListener("input", () => {
          valueDisplay.textContent =
            range.id === "headPoseThreshold"
              ? `${range.value}°`
              : range.value;
        });
      }
    });
  }
  
  function saveDetectionSettings() {
    // Get values from input fields
    const eyeThreshold = parseFloat(document.getElementById('eyeThreshold').value) || 0.15;
    const mouthThreshold = parseFloat(document.getElementById('mouthThreshold').value) || 1.35;
    const headPoseThreshold = parseFloat(document.getElementById('headPoseThreshold').value) || 10.0;
    
    // Create settings object
    const settings = {
      eye_threshold: eyeThreshold,
      mouth_threshold: mouthThreshold,
      head_pose_threshold: headPoseThreshold
    };
    
    // Update Current Detection UI immediately for a more responsive feel
    Detection.updateDetectionUI(settings);
    
    // Send settings to server
    AppState.getSocket().emit('update_detection_settings', settings);
    
    // Show success notification
    Notifications.showNotification('Detection settings saved successfully', 'success');
  }
  
  function resetDetectionSettings() {
    // Set default values
    const defaultSettings = {
      eye_threshold: 0.15,
      mouth_threshold: 1.35,
      head_pose_threshold: 10.0
    };
    
    // Update input fields with default values
    document.getElementById('eyeThreshold').value = defaultSettings.eye_threshold;
    document.getElementById('eyeThresholdValue').textContent = defaultSettings.eye_threshold;
    
    document.getElementById('mouthThreshold').value = defaultSettings.mouth_threshold;
    document.getElementById('mouthThresholdValue').textContent = defaultSettings.mouth_threshold;
    
    document.getElementById('headPoseThreshold').value = defaultSettings.head_pose_threshold;
    document.getElementById('headPoseThresholdValue').textContent = defaultSettings.head_pose_threshold + '°';
    
    // Update Current Detection UI
    Detection.updateDetectionUI(defaultSettings);
    
    // Send default settings to server
    AppState.getSocket().emit('update_detection_settings', defaultSettings);
    
    // Show success notification
    Notifications.showNotification('Detection settings reset to defaults', 'info');
  }
  
  function savePomodoroSettings() {
    // Get values from input fields
    const workDuration = parseInt(document.getElementById('workDuration').value) || 25;
    const shortBreakDuration = parseInt(document.getElementById('shortBreakDuration').value) || 5;
    const longBreakDuration = parseInt(document.getElementById('longBreakDuration').value) || 15;
    const sessionsBeforeLongBreak = parseInt(document.getElementById('sessionsBeforeLongBreak').value) || 4;
    
    // Validate inputs (ensure they're within reasonable ranges)
    const validatedSettings = {
      work_duration: Math.max(1, Math.min(60, workDuration)),
      short_break: Math.max(1, Math.min(30, shortBreakDuration)),
      long_break: Math.max(5, Math.min(60, longBreakDuration)),
      sessions_before_long_break: Math.max(1, Math.min(10, sessionsBeforeLongBreak))
    };
    
    // Send settings to server
    AppState.getSocket().emit('update_pomodoro_settings', validatedSettings);
    
    // Show success notification
    Notifications.showNotification('Pomodoro settings saved successfully', 'success');
    
    // Update input fields with validated values
    document.getElementById('workDuration').value = validatedSettings.work_duration;
    document.getElementById('shortBreakDuration').value = validatedSettings.short_break;
    document.getElementById('longBreakDuration').value = validatedSettings.long_break;
    document.getElementById('sessionsBeforeLongBreak').value = validatedSettings.sessions_before_long_break;
    
    // Update the timer display immediately
    Pomodoro.updateTimerDisplay();
  }
  
  function resetPomodoroSettings() {
    // Set default values
    const defaultSettings = {
      work_duration: 25,
      short_break: 5,
      long_break: 15,
      sessions_before_long_break: 4
    };
    
    // Update input fields with default values
    document.getElementById('workDuration').value = defaultSettings.work_duration;
    document.getElementById('shortBreakDuration').value = defaultSettings.short_break;
    document.getElementById('longBreakDuration').value = defaultSettings.long_break;
    document.getElementById('sessionsBeforeLongBreak').value = defaultSettings.sessions_before_long_break;
    
    // Send default settings to server
    AppState.getSocket().emit('update_pomodoro_settings', defaultSettings);
    
    // Show success notification
    Notifications.showNotification('Pomodoro settings reset to defaults', 'info');
    
    // Update the timer display immediately
    Pomodoro.updateTimerDisplay();
  }

  // Public methods
  return {
    setupRangeInputs: setupRangeInputs,
    
    setupButtons: function() {
      // Detection settings buttons
      const detectionSaveBtn = document.querySelector('#settings-section .bg-white:nth-child(1) button.bg-blue-600');
      const detectionResetBtn = document.querySelector('#settings-section .bg-white:nth-child(1) button.border-gray-300');
      
      if (detectionSaveBtn) detectionSaveBtn.addEventListener('click', saveDetectionSettings);
      if (detectionResetBtn) detectionResetBtn.addEventListener('click', resetDetectionSettings);
      
      // Pomodoro settings buttons
      const pomodoroSaveBtn = document.querySelector('#settings-section .bg-white:nth-child(2) button.bg-blue-600');
      const pomodoroResetBtn = document.querySelector('#settings-section .bg-white:nth-child(2) button.border-gray-300');
      
      if (pomodoroSaveBtn) pomodoroSaveBtn.addEventListener('click', savePomodoroSettings);
      if (pomodoroResetBtn) pomodoroResetBtn.addEventListener('click', resetPomodoroSettings);
    },
    
    handleSettingsUpdate: function(response) {
      // Show a notification
      if (response.status === "success") {
        Notifications.showNotification(response.message, "success");
      } else {
        Notifications.showNotification(`Error: ${response.message}`, "error");
      }
    },
    
    updateUIFromSettings: function(settings) {
      if (settings.detection) {
        // Update detection settings inputs
        const eyeThreshold = document.getElementById("eyeThreshold");
        const eyeThresholdValue = document.getElementById("eyeThresholdValue");
        
        if (eyeThreshold && eyeThresholdValue) {
          eyeThreshold.value = settings.detection.eye_threshold;
          eyeThresholdValue.textContent = settings.detection.eye_threshold;
        }

        const mouthThreshold = document.getElementById("mouthThreshold");
        const mouthThresholdValue = document.getElementById("mouthThresholdValue");
        
        if (mouthThreshold && mouthThresholdValue) {
          mouthThreshold.value = settings.detection.mouth_threshold;
          mouthThresholdValue.textContent = settings.detection.mouth_threshold;
        }

        const headPoseThreshold = document.getElementById("headPoseThreshold");
        const headPoseThresholdValue = document.getElementById("headPoseThresholdValue");
        
        if (headPoseThreshold && headPoseThresholdValue) {
          headPoseThreshold.value = settings.detection.head_pose_threshold;
          headPoseThresholdValue.textContent = `${settings.detection.head_pose_threshold}°`;
        }
        
        // Update Current Detection UI
        Detection.updateDetectionUI(settings.detection);
      }

      if (settings.pomodoro) {
        // Update pomodoro settings inputs
        const workDuration = document.getElementById("workDuration");
        const shortBreakDuration = document.getElementById("shortBreakDuration");
        const longBreakDuration = document.getElementById("longBreakDuration");
        const sessionsBeforeLongBreak = document.getElementById("sessionsBeforeLongBreak");
        
        if (workDuration) workDuration.value = settings.pomodoro.work_duration;
        if (shortBreakDuration) shortBreakDuration.value = settings.pomodoro.short_break;
        if (longBreakDuration) longBreakDuration.value = settings.pomodoro.long_break;
        if (sessionsBeforeLongBreak) sessionsBeforeLongBreak.value = settings.pomodoro.sessions_before_long_break;
      }
    }
  };
})();

// Export the Settings namespace
window.Settings = Settings;