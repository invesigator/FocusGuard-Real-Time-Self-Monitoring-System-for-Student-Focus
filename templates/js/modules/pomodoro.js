/**
 * Client-side timer enhancement for pomodoro.js
 * This adds a client-side timer that runs parallel to the server updates
 * to ensure the UI is always updated even if server messages are delayed
 */

const Pomodoro = (function() {
  // Private variables for client-side timer
  let clientTimerInterval = null;
  let lastTimerData = null;
  let clientEndTime = null;
  
  // Private methods
  function startPomodoro() {
    // Add a visual "press" effect to the button
    const startBtn = document.getElementById("pomodoroStartBtn");
    if (startBtn) {
      startBtn.classList.add("button-pressed");
      setTimeout(() => {
        startBtn.classList.remove("button-pressed");
      }, 200);
    }
    
    // Add subtle pulse animation to timer
    const timerContainer = document.querySelector(".timer-display-container");
    if (timerContainer) {
      timerContainer.classList.add("timer-active");
    }
    
    // Check if the timer is already active but paused
    const pauseBtn = document.getElementById("pomodoroPauseBtn");
    const isPaused = AppState.isPomodoroActive() && pauseBtn && pauseBtn.disabled;
    
    if (isPaused) {
      // If timer is paused, resume it instead of starting a new one
      AppState.getSocket().emit("pomodoro_start"); // This will call the resume functionality in your Python code
    } else {
      // Otherwise start a new timer with the current mode
      AppState.getSocket().emit("pomodoro_custom_start", { mode: AppState.getCurrentTimerMode() });
    }
  }
  
  function pausePomodoro() {
    // Add a visual "press" effect to the button
    const pauseBtn = document.getElementById("pomodoroPauseBtn");
    if (pauseBtn) {
      pauseBtn.classList.add("button-pressed");
      setTimeout(() => {
        pauseBtn.classList.remove("button-pressed");
      }, 200);
    }
    
    // Remove pulse animation
    const timerContainer = document.querySelector(".timer-display-container");
    if (timerContainer) {
      timerContainer.classList.remove("timer-active");
    }
    
    // Clear the client-side timer interval
    stopClientTimer();
    
    // Emit socket event
    AppState.getSocket().emit("pomodoro_pause");
  }
  
  function stopPomodoro() {
    // Add a visual "press" effect to the button
    const stopBtn = document.getElementById("pomodoroStopBtn");
    if (stopBtn) {
      stopBtn.classList.add("button-pressed");
      setTimeout(() => {
        stopBtn.classList.remove("button-pressed");
      }, 200);
    }
    
    // Remove pulse animation
    const timerContainer = document.querySelector(".timer-display-container");
    if (timerContainer) {
      timerContainer.classList.remove("timer-active");
    }
    
    // Clear the client-side timer
    stopClientTimer();
    
    // Reset timer progress with quick animation
    updateTimerProgress(100);
    
    // Emit socket event
    AppState.getSocket().emit("pomodoro_stop");
  }
  
  // Start the client-side timer for continuous updates
  function startClientTimer(data) {
    // First, clear any existing timer
    stopClientTimer();
    
    if (!data || !data.active || data.paused) {
      return; // Don't start client timer if timer is not active or is paused
    }
    
    // Parse the remaining time
    const [minutes, seconds] = data.time_remaining.split(":").map(Number);
    const remainingSeconds = minutes * 60 + seconds;
    
    // Set the end time based on current time plus remaining seconds
    clientEndTime = new Date(Date.now() + remainingSeconds * 1000);
    
    // Store the last timer data for reference
    lastTimerData = {...data};
    
    // Start an interval to update the display every 500ms
    clientTimerInterval = setInterval(() => {
      updateClientTimer();
    }, 500);
    
    console.log("Client-side timer started, end time:", clientEndTime);
  }
  
  // Stop the client-side timer
  function stopClientTimer() {
    if (clientTimerInterval) {
      clearInterval(clientTimerInterval);
      clientTimerInterval = null;
      clientEndTime = null;
      console.log("Client-side timer stopped");
    }
  }
  
  // Update the timer display based on client-side time calculation
  function updateClientTimer() {
    if (!clientEndTime || !lastTimerData) return;
    
    // Calculate remaining time
    const now = new Date();
    const diff = Math.max(0, Math.floor((clientEndTime - now) / 1000));
    
    // Format the time
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    // Update the display
    const timerDisplay = document.getElementById("timerDisplay");
    if (timerDisplay) {
      timerDisplay.textContent = timeString;
    }
    
    // Update progress circle
    if (lastTimerData.session_type === "work") {
      const totalSeconds = parseInt(document.getElementById('workDuration').value || 25) * 60;
      const progressPercentage = (diff / totalSeconds) * 100;
      updateTimerProgress(progressPercentage);
    } else if (lastTimerData.session_type === "short_break") {
      const totalSeconds = parseInt(document.getElementById('shortBreakDuration').value || 5) * 60;
      const progressPercentage = (diff / totalSeconds) * 100;
      updateTimerProgress(progressPercentage);
    } else if (lastTimerData.session_type === "long_break") {
      const totalSeconds = parseInt(document.getElementById('longBreakDuration').value || 15) * 60;
      const progressPercentage = (diff / totalSeconds) * 100;
      updateTimerProgress(progressPercentage);
    }
    
    // If timer has ended (diff is 0), trigger a sync with the server
    if (diff === 0) {
      console.log("Client timer reached 0, requesting timer status update");
      AppState.getSocket().emit("get_timer_status");
      stopClientTimer();
    }
  }
  
  function switchTimerMode(mode) {
    // If timer is running, confirm with user before switching
    if (AppState.isPomodoroActive()) {
      if (!confirm("Changing the timer mode will reset your current session. Continue?")) {
        return;
      }
      
      // Stop the current timer
      stopPomodoro();
    }
    
    // Set the new timer mode
    setTimerModeWithCustomSettings(mode);
    
    // Update the display with animation
    updateTimerDisplayWithAnimation(mode);
  }
  
  function setTimerModeWithCustomSettings(mode) {
    const pomodoroModeBtn = document.getElementById("pomodoroModeBtn");
    const shortBreakModeBtn = document.getElementById("shortBreakModeBtn");
    const longBreakModeBtn = document.getElementById("longBreakModeBtn");
    const timerDisplay = document.getElementById("timerDisplay");
    const sessionTypeDisplay = document.getElementById("sessionTypeDisplay");
    const timerContainer = document.querySelector(".timer-display-container");
    const timerCircle = document.getElementById("timerCircle");
    
    // Get current custom settings
    const workDuration = parseInt(document.getElementById('workDuration').value) || 25;
    const shortBreakDuration = parseInt(document.getElementById('shortBreakDuration').value) || 5;
    const longBreakDuration = parseInt(document.getElementById('longBreakDuration').value) || 15;
    
    // Remove active class from all buttons
    pomodoroModeBtn.classList.remove("active");
    shortBreakModeBtn.classList.remove("active");
    longBreakModeBtn.classList.remove("active");
    
    // Fade out current mode (add transition class)
    timerContainer.classList.add("mode-transition");
    
    // Remove all timer mode classes after a short delay
    setTimeout(() => {
      timerContainer.classList.remove("timer-pomodoro", "timer-short-break", "timer-long-break");
      
      // Set active class and timer display based on mode
      switch(mode) {
        case "pomodoro":
          pomodoroModeBtn.classList.add("active");
          timerContainer.classList.add("timer-pomodoro");
          // Format minutes with leading zero if needed
          const formattedWorkDuration = workDuration < 10 ? `0${workDuration}` : workDuration;
          timerDisplay.textContent = `${formattedWorkDuration}:00`;
          sessionTypeDisplay.textContent = "Work Session";
          AppState.setCurrentTimerMode("pomodoro");
          break;
        case "short-break":
          shortBreakModeBtn.classList.add("active");
          timerContainer.classList.add("timer-short-break");
          // Format minutes with leading zero if needed
          const formattedShortBreakDuration = shortBreakDuration < 10 ? `0${shortBreakDuration}` : shortBreakDuration;
          timerDisplay.textContent = `${formattedShortBreakDuration}:00`;
          sessionTypeDisplay.textContent = "Short Break";
          AppState.setCurrentTimerMode("short-break");
          break;
        case "long-break":
          longBreakModeBtn.classList.add("active");
          timerContainer.classList.add("timer-long-break");
          // Format minutes with leading zero if needed
          const formattedLongBreakDuration = longBreakDuration < 10 ? `0${longBreakDuration}` : longBreakDuration;
          timerDisplay.textContent = `${formattedLongBreakDuration}:00`;
          sessionTypeDisplay.textContent = "Long Break";
          AppState.setCurrentTimerMode("long-break");
          break;
      }
      
      // Update timer mode indicator
      updateModeIndicator(mode);
      
      // Reset timer progress circle with animation
      updateTimerProgress(100);
      
      // Remove the transition class after animation completes
      setTimeout(() => {
        timerContainer.classList.remove("mode-transition");
      }, 300);
    }, 150);
  }
  
  function setActiveModeButton(mode) {
    const pomodoroModeBtn = document.getElementById("pomodoroModeBtn");
    const shortBreakModeBtn = document.getElementById("shortBreakModeBtn");
    const longBreakModeBtn = document.getElementById("longBreakModeBtn");
    
    if (!pomodoroModeBtn || !shortBreakModeBtn || !longBreakModeBtn) return;
    
    // Remove active class from all buttons
    pomodoroModeBtn.classList.remove("active");
    shortBreakModeBtn.classList.remove("active");
    longBreakModeBtn.classList.remove("active");
    
    // Add active class to the current mode button
    if (mode === "pomodoro") {
      pomodoroModeBtn.classList.add("active");
      AppState.setCurrentTimerMode("pomodoro");
    } else if (mode === "short-break") {
      shortBreakModeBtn.classList.add("active");
      AppState.setCurrentTimerMode("short-break");
    } else if (mode === "long-break") {
      longBreakModeBtn.classList.add("active");
      AppState.setCurrentTimerMode("long-break");
    }
  }
  
  function updateTimerDisplayWithAnimation(mode) {
    const timerContainer = document.querySelector(".timer-display-container");
    const modeIndicator = document.querySelector(".timer-mode-indicator");

    // Define the text and colors for each mode
    const modeSettings = {
      "pomodoro": {
        text: "FOCUS TIME",
        color: "#4361ee"
      },
      "short-break": {
        text: "SHORT BREAK",
        color: "#06d6a0"
      },
      "long-break": {
        text: "LONG BREAK",
        color: "#9b5de5"
      }
    };

    // Update the mode indicator text and color
    if (modeIndicator) {
      modeIndicator.textContent = modeSettings[mode].text;
      modeIndicator.style.backgroundColor = modeSettings[mode].color;
    } else {
      // Create a new indicator if it doesn't exist
      createModeIndicator(mode, timerContainer);
    }
  }
  
  function updateModeIndicator(mode) {
    const timerContainer = document.querySelector(".timer-display-container");
    
    // Remove any existing indicator
    const existingIndicator = document.querySelector(".timer-mode-indicator");
    if (existingIndicator) {
      // Fade out
      existingIndicator.style.opacity = "0";
      setTimeout(() => {
        existingIndicator.remove();
        
        // Create and fade in new indicator
        createModeIndicator(mode, timerContainer);
      }, 200);
    } else {
      // Create new indicator
      createModeIndicator(mode, timerContainer);
    }
  }
  
  function createModeIndicator(mode, container) {
    if (!container) return;
    
    let indicatorText = "";
    let indicatorColor = "";
    
    switch(mode) {
      case "pomodoro":
        indicatorText = "FOCUS TIME";
        indicatorColor = "#4361ee"; // Improved blue
        break;
      case "short-break":
        indicatorText = "SHORT BREAK";
        indicatorColor = "#06d6a0"; // Fresh teal
        break;
      case "long-break":
        indicatorText = "LONG BREAK";
        indicatorColor = "#9b5de5"; // Vibrant purple
        break;
    }
    
    // Remove any existing indicator to prevent duplicates
    const existingIndicator = document.querySelector(".timer-mode-indicator");
    if (existingIndicator) {
      existingIndicator.remove();
    }
    
    const indicator = document.createElement("div");
    indicator.className = "timer-mode-indicator";
    indicator.textContent = indicatorText;
    indicator.style.backgroundColor = indicatorColor;
    indicator.style.color = "white";
    
    container.appendChild(indicator);
    
    // Make sure the indicator is visible
    indicator.style.opacity = "1";
    indicator.style.transition = "opacity 0.3s ease";
  }
  
  function updateTimerProgress(percentage) {
    const circle = document.getElementById("timerCircle");
    if (!circle) return;
    
    const radius = parseInt(circle.getAttribute("r"));
    const circumference = 2 * Math.PI * radius;

    // Ensure circle has the proper transition
    circle.style.transition = "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)";
    
    // Set the dash array
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    
    // Calculate the dash offset
    const offset = circumference - (percentage / 100) * circumference;
    
    // Apply the dash offset with a small delay to ensure animation runs
    setTimeout(() => {
      circle.style.strokeDashoffset = offset;
    }, 50);
  }
  
  function updateTimerDisplayFromSettings() {
    // Get the current timer mode
    let mode = "pomodoro";
    
    if (document.getElementById("shortBreakModeBtn") && 
        document.getElementById("shortBreakModeBtn").classList.contains("active")) {
      mode = "short-break";
    } else if (document.getElementById("longBreakModeBtn") && 
              document.getElementById("longBreakModeBtn").classList.contains("active")) {
      mode = "long-break";
    }
    
    // Get the current settings values
    const workDuration = parseInt(document.getElementById('workDuration').value) || 25;
    const shortBreakDuration = parseInt(document.getElementById('shortBreakDuration').value) || 5;
    const longBreakDuration = parseInt(document.getElementById('longBreakDuration').value) || 15;
    
    // Get display elements
    const timerDisplay = document.getElementById("timerDisplay");
    
    // Only update if the timer is not currently active
    if (!AppState.isPomodoroActive() && timerDisplay) {
      // Format the time based on current mode
      let minutes = 0;
      if (mode === "pomodoro") {
        minutes = workDuration;
      } else if (mode === "short-break") {
        minutes = shortBreakDuration;
      } else if (mode === "long-break") {
        minutes = longBreakDuration;
      }
      
      // Format the display time (e.g., "25:00")
      timerDisplay.textContent = `${minutes < 10 ? '0' + minutes : minutes}:00`;
    }
  }
  
  function handlePomodoroUpdate(data) {
    const timerDisplay = document.getElementById("timerDisplay");
    const sessionTypeDisplay = document.getElementById("sessionTypeDisplay");
    const sessionsCompleted = document.getElementById("sessionsCompleted");
    const timerContainer = document.querySelector(".timer-display-container");
    
    if (!timerDisplay || !sessionTypeDisplay || !sessionsCompleted) return;

    timerDisplay.textContent = data.time_remaining;

    // Calculate progress percentage based on session type and time remaining
    let totalSeconds = 0;
    let remainingSeconds = 0;
    let currentMode = "";

    if (data.active) {
      const [minutes, seconds] = data.time_remaining.split(":").map(Number);
      remainingSeconds = minutes * 60 + seconds;

      if (data.session_type === "work") {
        totalSeconds = parseInt(document.getElementById('workDuration').value || 25) * 60;
        currentMode = "pomodoro";
        // Update the active mode button
        if (document.getElementById("pomodoroModeBtn")) {
          setActiveModeButton("pomodoro");
          if (timerContainer) {
            timerContainer.classList.remove("timer-short-break", "timer-long-break");
            timerContainer.classList.add("timer-pomodoro");
          }
        }
      } else if (data.session_type === "short_break") {
        totalSeconds = parseInt(document.getElementById('shortBreakDuration').value || 5) * 60;
        currentMode = "short-break";
        // Update the active mode button
        if (document.getElementById("shortBreakModeBtn")) {
          setActiveModeButton("short-break");
          if (timerContainer) {
            timerContainer.classList.remove("timer-pomodoro", "timer-long-break");
            timerContainer.classList.add("timer-short-break");
          }
        }
      } else if (data.session_type === "long_break") {
        totalSeconds = parseInt(document.getElementById('longBreakDuration').value || 15) * 60;
        currentMode = "long-break";
        // Update the active mode button
        if (document.getElementById("longBreakModeBtn")) {
          setActiveModeButton("long-break");
          if (timerContainer) {
            timerContainer.classList.remove("timer-pomodoro", "timer-short-break");
            timerContainer.classList.add("timer-long-break");
          }
        }
      }

      // Update the mode indicator
      if (currentMode) {
        updateTimerDisplayWithAnimation(currentMode);
      }

      // Update progress circle
      const progressPercentage = (remainingSeconds / totalSeconds) * 100;
      updateTimerProgress(progressPercentage);
      
      // Start or update client-side timer
      if (!data.paused) {
        startClientTimer(data);
      } else {
        stopClientTimer();
      }
    } else {
      // Reset progress circle
      updateTimerProgress(100);
      // Stop client timer
      stopClientTimer();
    }

    // Update session type display
    let sessionTypeText = "Work Session";
    if (data.session_type === "short_break") {
      sessionTypeText = "Short Break";
    } else if (data.session_type === "long_break") {
      sessionTypeText = "Long Break";
    }

    if (data.paused) {
      sessionTypeText += " (Paused)";
    }

    sessionTypeDisplay.textContent = sessionTypeText;
    sessionsCompleted.textContent = data.sessions_completed || 0;

    AppState.setPomodoroActive(data.active);

    const startBtn = document.getElementById("pomodoroStartBtn");
    const pauseBtn = document.getElementById("pomodoroPauseBtn");
    const stopBtn = document.getElementById("pomodoroStopBtn");

    if (data.active) {
      if (startBtn) {
        startBtn.disabled = !data.paused;
        // Keep only the icon
        startBtn.innerHTML = '<i class="fas fa-play"></i>';
      }
      if (pauseBtn) pauseBtn.disabled = data.paused;
      if (stopBtn) stopBtn.disabled = false;
    } else {
      if (startBtn) {
        startBtn.disabled = false;
        // Keep only the icon
        startBtn.innerHTML = '<i class="fas fa-play"></i>';
      }
      if (pauseBtn) pauseBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = true;
    }
  }

  // Public methods
  return {
    setupButtons: function() {
      const startBtn = document.getElementById("pomodoroStartBtn");
      const pauseBtn = document.getElementById("pomodoroPauseBtn");
      const stopBtn = document.getElementById("pomodoroStopBtn");
      
      if (startBtn) startBtn.addEventListener("click", startPomodoro);
      if (pauseBtn) pauseBtn.addEventListener("click", pausePomodoro);
      if (stopBtn) stopBtn.addEventListener("click", stopPomodoro);
    },
    
    setupModeButtons: function() {
      const pomodoroModeBtn = document.getElementById("pomodoroModeBtn");
      const shortBreakModeBtn = document.getElementById("shortBreakModeBtn");
      const longBreakModeBtn = document.getElementById("longBreakModeBtn");
      const timerContainer = document.querySelector(".timer-display-container") || 
                              document.querySelector("svg").parentElement;
      
      if (!pomodoroModeBtn || !shortBreakModeBtn || !longBreakModeBtn) return;

      // Add timer-display-container class to the timer container if it doesn't have it
      if (timerContainer && !timerContainer.classList.contains("timer-display-container")) {
        timerContainer.classList.add("timer-display-container");
      }
      
      // Initially set to pomodoro mode
      setTimerModeWithCustomSettings("pomodoro");
      
      // Set up event listeners for mode buttons
      pomodoroModeBtn.addEventListener("click", () => switchTimerMode("pomodoro"));
      shortBreakModeBtn.addEventListener("click", () => switchTimerMode("short-break"));
      longBreakModeBtn.addEventListener("click", () => switchTimerMode("long-break"));
    },
    
    setupIconOnlyButtons: function() {
      // Get the button elements
      const startBtn = document.getElementById("pomodoroStartBtn");
      const pauseBtn = document.getElementById("pomodoroPauseBtn");
      const stopBtn = document.getElementById("pomodoroStopBtn");
      
      if (startBtn) {
        // Ensure start button has ONLY the icon with no text
        startBtn.innerHTML = '<i class="fas fa-play"></i>';
        startBtn.classList.add("icon-button");
        // Remove any text nodes that might be present
        Array.from(startBtn.childNodes).forEach(node => {
          if (node.nodeType === Node.TEXT_NODE) {
            startBtn.removeChild(node);
          }
        });
      }
      
      if (pauseBtn) {
        pauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        pauseBtn.classList.add("icon-button");
      }
      
      if (stopBtn) {
        stopBtn.innerHTML = '<i class="fas fa-stop"></i>';
        stopBtn.classList.add("icon-button");
      }
    },
    
    updateTimerDisplay: updateTimerDisplayFromSettings,
    handleTimerUpdate: handlePomodoroUpdate,
    updateTimerProgress: updateTimerProgress
  };
})();

// Export the Pomodoro namespace
window.Pomodoro = Pomodoro;