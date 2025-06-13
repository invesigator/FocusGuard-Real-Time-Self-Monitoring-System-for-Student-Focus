/**
 * notifications.js
 * Handles notification and alert functionality
 */

const Notifications = (function() {
  // Private methods
  function showNotification(message, type = "info") {
    // Define icon mapping
    const iconMap = {
      success: "check-circle",
      error: "exclamation-circle",
      warning: "exclamation-triangle",
      info: "info-circle"
    };
    
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg transition-opacity duration-500 z-50 flex items-center`;

    // Set background color based on type
    if (type === "success") {
      notification.classList.add("bg-green-500", "text-white");
    } else if (type === "error") {
      notification.classList.add("bg-red-500", "text-white");
    } else if (type === "warning") {
      notification.classList.add("bg-yellow-500", "text-white");
    } else {
      notification.classList.add("bg-blue-500", "text-white");
    }

    // Add icon based on type
    const icon = iconMap[type] || "info-circle";

    notification.innerHTML = `
      <div class="flex items-center">
        <i class="fas fa-${icon} text-lg mr-3"></i>
        <div>
          <span class="font-medium">${message}</span>
        </div>
        <button class="ml-4 text-white opacity-75 hover:opacity-100 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;

    // Add to document
    document.body.appendChild(notification);

    // Set initial opacity to 0
    notification.style.opacity = "0";
    
    // Trigger animation after a small delay
    setTimeout(() => {
      notification.style.opacity = "1";
    }, 10);

    // Remove after 5 seconds unless it's an error
    const timeout = type === "error" ? 8000 : 5000;
    setTimeout(() => {
      notification.style.opacity = "0";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 500);
    }, timeout);
  }
  
  function playNotificationSound(type) {
    try {
      let audio;
      switch(type) {
        case 'drowsy':
          audio = new Audio('assets/audio/wake_up_sir.wav');
          break;
        case 'yawn':
          audio = new Audio('assets/audio/take_some_fresh_air_sir.wav');
          break;
        case 'distraction':
          audio = new Audio('assets/audio/stay_focus.wav');
          break;
        case 'camera_blocked':
          audio = new Audio('assets/audio/camera_blocked.wav');
          break;
        default:
          return;
      }
      
      audio.volume = 0.6;
      audio.play();
    } catch(e) {
      console.error("Error playing notification sound:", e);
    }
  }
  
  function playAchievementSound() {
    try {
      const audio = new Audio('assets/audio/achievement.wav');
      audio.volume = 0.5;
      audio.play();
    } catch(e) {
      console.error("Error playing achievement sound:", e);
    }
  }
  
  function playRewardSound(type) {
    try {
      let soundFile = 'achievement.wav';
      
      switch(type) {
        case 'level':
          soundFile = 'level_up.wav';
          break;
        case 'points':
          soundFile = 'points.wav';
          break;
        case 'streak':
          soundFile = 'streak.wav';
          break;
        case 'badge':
          soundFile = 'badge.wav';
          break;
      }
      
      const audio = new Audio(`assets/audio/${soundFile}`);
      audio.volume = 0.5;
      audio.play();
    } catch(e) {
      console.error(`Error playing ${type} sound:`, e);
    }
  }
  
  function showRewardNotification(options) {
    // Default options
    const defaults = {
      title: 'Reward Earned!',
      message: 'You earned a reward!',
      points: null,
      type: 'points',
      duration: 5000
    };
    
    // Merge defaults with provided options
    const settings = { ...defaults, ...options };
    
    // Create notification element if it doesn't exist
    let notification = document.querySelector('.reward-notification');
    if (!notification) {
      notification = document.createElement('div');
      notification.className = 'reward-notification';
      document.body.appendChild(notification);
    }
    
    // Set icon based on type
    let icon = 'trophy';
    switch(settings.type) {
      case 'achievement':
        icon = 'award';
        break;
      case 'level':
        icon = 'level-up-alt';
        break;
      case 'points':
        icon = 'star';
        break;
      case 'streak':
        icon = 'fire';
        break;
      case 'badge':
        icon = 'shield-alt';
        break;
    }
    
    // Set content
    let pointsHtml = settings.points ? `<div class="reward-notification__points">+${settings.points} points</div>` : '';
    
    notification.innerHTML = `
      <div class="flex items-start">
        <div class="mr-3">
          <i class="fas fa-${icon} text-2xl"></i>
        </div>
        <div class="flex-grow">
          <div class="reward-notification__title">${settings.title}</div>
          <div class="reward-notification__message">${settings.message}</div>
          ${pointsHtml}
        </div>
        <button class="ml-3 text-white opacity-75 hover:opacity-100 focus:outline-none" onclick="this.parentElement.parentElement.classList.remove('show')">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
    
    // Show the notification
    setTimeout(() => {
      notification.classList.add('show');
    }, 100);
    
    // Play sound based on type
    playRewardSound(settings.type);
    
    // Auto-remove after duration
    if (settings.duration) {
      setTimeout(() => {
        notification.classList.remove('show');
      }, settings.duration);
    }
  }
  
  // Public methods
  return {
    showNotification: showNotification,
    playNotificationSound: playNotificationSound,
    playAchievementSound: playAchievementSound,
    showRewardNotification: showRewardNotification,
    
    showPointsAnimation: function(points) {
      if (points <= 0) return;
      
      // Create a floating element that animates upward
      const pointsEl = document.createElement('div');
      pointsEl.className = 'fixed z-50 text-lg font-bold text-blue-600 points-animation';
      pointsEl.textContent = `+${points} points`;
      
      // Position near the header
      const header = document.querySelector('header');
      if (header) {
        const rect = header.getBoundingClientRect();
        pointsEl.style.top = `${rect.bottom + 20}px`;
        pointsEl.style.right = `${window.innerWidth - rect.right + 20}px`;
      } else {
        pointsEl.style.top = '100px';
        pointsEl.style.right = '20px';
      }
      
      // Add to body and then remove after animation
      document.body.appendChild(pointsEl);
      
      setTimeout(() => {
        pointsEl.remove();
      }, 2000);
    },
    
    createConfetti: function(count = 50) {
      const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];
      
      for (let i = 0; i < count; i++) {
        // Create a confetti element
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        
        // Randomize properties
        const color = colors[Math.floor(Math.random() * colors.length)];
        const left = Math.random() * 100;
        const width = Math.random() * 10 + 5;
        const height = Math.random() * 10 + 5;
        const delay = Math.random() * 3;
        
        // Apply styles
        confetti.style.backgroundColor = color;
        confetti.style.left = `${left}vw`;
        confetti.style.width = `${width}px`;
        confetti.style.height = `${height}px`;
        confetti.style.opacity = Math.random() + 0.5;
        confetti.style.animationDelay = `${delay}s`;
        
        // Add to body
        document.body.appendChild(confetti);
        
        // Remove after animation completes
        setTimeout(() => {
          confetti.remove();
        }, 4000 + delay * 1000);
      }
    }
  };
})();

// Export the Notifications namespace
window.Notifications = Notifications;