/**
 * gamification.js
 * Handles gamification, achievements, and rewards system
 */

const Gamification = (function() {
  // Private methods
  function updateGamificationUI(data) {
    if (data.error) {
        console.error("Error updating gamification UI:", data.error);
        return;
    }
    
    console.log("Received gamification data:", data);
      
    // Update level and points
    const userLevel = document.getElementById('userLevel');
    const nextLevel = document.getElementById('nextLevel');
    const userPoints = document.getElementById('userPoints');
    
    if (userLevel) userLevel.textContent = data.level || 1;
    if (nextLevel) nextLevel.textContent = (data.level || 1) + 1;
    if (userPoints) userPoints.textContent = (data.points || 0).toLocaleString();
    
    // Update progress bar - FIX for progress bar calculation
    const progressBar = document.getElementById('levelProgressBar');
    const xpProgress = document.getElementById('xpProgress');
    
    // Make sure progress is correctly calculated and never 100% unless at max level
    let progressPercentage = 0;
    
    if (data.xp_progress !== undefined) {
        // If the backend provides the percentage, use it directly but ensure it's reasonable
        progressPercentage = Math.min(Math.max(data.xp_progress, 0), 99.9);
        
        // Only show 100% if specifically at max level
        const maxLevel = 50; // Assuming 50 is the max level
        if (data.level >= maxLevel) {
            progressPercentage = 100;
        }
    } else {
        // Calculate based on current experience and level thresholds
        const currentLevel = data.level || 1;
        const nextLevelAt = data.next_level_at || (currentLevel * 300);
        const currentXP = data.experience || 0;
        
        // Use a rolling calculation that ensures progress is between 0-99.9%
        // We want progress % to reflect progress to next level
        const baseXP = (currentLevel - 1) * 300; // Simple calculation based on level
        const nextLevelXP = baseXP + 300;        // Next level requires 300 more XP
        
        const levelProgress = currentXP - baseXP;
        const requiredForLevel = nextLevelXP - baseXP;
        
        // Calculate percentage but keep it under 100% unless at max level
        progressPercentage = Math.min((levelProgress / requiredForLevel) * 100, 99.9);
        
        // Only show 100% if specifically at max level
        if (currentLevel >= 50) { // Assuming 50 is max level
            progressPercentage = 100;
        }
    }
    
    // Apply the corrected progress to UI elements
    if (progressBar) {
        progressBar.style.width = `${progressPercentage}%`;
        console.log(`Setting progress bar width to ${progressPercentage}%`);
    }
    
    if (xpProgress) {
        xpProgress.textContent = `${Math.round(progressPercentage)}%`;
    }
    
    // Update streaks
    const dailyStreak = document.getElementById('dailyStreak');
    const pomodoroStreak = document.getElementById('pomodoroStreak');
    
    if (dailyStreak) {
        const streak = data.daily_streak || 0;
        dailyStreak.textContent = `${streak} day${streak !== 1 ? 's' : ''}`;
    }
    
    if (pomodoroStreak) {
        const streak = data.pomodoro_streak || 0;
        pomodoroStreak.textContent = `${streak} session${streak !== 1 ? 's' : ''}`;
    }
    
    // Rest of the function remains unchanged...
    
    // Update achievements progress
    const achievementProgress = document.getElementById('achievementProgress');
    if (achievementProgress) {
        achievementProgress.textContent = `${data.achievements?.completed || 0}/${data.achievements?.total || 0}`;
    }
    
    // Update badges progress
    const badgeProgress = document.getElementById('badgeProgress');
    if (badgeProgress) {
        badgeProgress.textContent = `${data.badges?.unlocked || 0}/${data.badges?.total || 0}`;
    }
    
    // Render achievements list
    renderAchievements(data.achievement_list || []);
    
    // Render badges list
    renderBadges(data.badge_list || []);
    
    // Update level title based on level
    const levelTitle = document.querySelector('.text-lg.font-semibold.text-gray-800');
    if (levelTitle) {
        if (data.level < 5) {
            levelTitle.textContent = "Focus Apprentice";
        } else if (data.level < 10) {
            levelTitle.textContent = "Focus Adept";
        } else if (data.level < 15) {
            levelTitle.textContent = "Focus Expert";
        } else if (data.level < 20) {
            levelTitle.textContent = "Focus Master";
        } else {
            levelTitle.textContent = "Focus Grandmaster";
        }
    }
    
    // Fix 2: Ensure the check-in button is visible by explicitly setting its styles
    ensureCheckInButtonVisible();
  }

  function ensureCheckInButtonVisible() {
    const checkInBtn = document.getElementById('dailyCheckInBtn');
    if (checkInBtn) {
      // Force visibility with comprehensive styling
      checkInBtn.style.display = 'flex';
      checkInBtn.style.opacity = '1';
      checkInBtn.style.visibility = 'visible';
      checkInBtn.style.backgroundColor = '#f97316'; // Hex for bg-orange-500
      checkInBtn.style.color = '#ffffff';           // White text
      checkInBtn.style.position = 'relative';       // Ensure it’s not overlapped
      checkInBtn.style.zIndex = '10';               // Bring forward if needed
      
      // Ensure Tailwind classes are applied correctly
      if (!checkInBtn.classList.contains('bg-orange-500')) {
        checkInBtn.classList.add('bg-orange-500', 'text-white');
        checkInBtn.classList.remove('bg-gray-500');
      }
      
      console.log("Check-in button visibility enforced");
    } else {
      console.warn("Check-in button not found in DOM");
    }
  }
  
  function renderAchievements(achievements) {
    const container = document.getElementById('achievementsList');
    if (!container) {
      console.warn("Achievements container not found");
      return;
    }
    
    // If no achievements or empty array, show placeholders
    if (!achievements || !achievements.length) {
      console.log("No achievements data, showing placeholders");
      container.innerHTML = `
        <div class="flex items-start p-3 rounded-lg bg-gray-50 border border-gray-200">
          <div class="bg-gray-200 w-12 h-12 rounded-full flex items-center justify-center mr-4">
            <i class="fas fa-lock text-gray-400"></i>
          </div>
          <div class="flex-grow">
            <div class="flex justify-between items-start">
              <h4 class="font-medium text-gray-800">First Steps</h4>
              <span class="text-xs font-semibold text-gray-400">+50 pts</span>
            </div>
            <p class="text-sm text-gray-500">Complete your first focus session</p>
          </div>
        </div>
      `;
      return;
    }
    
    let html = '';
    
    achievements.forEach(achievement => {
      const completedClass = achievement.completed ? 'bg-blue-100 border-blue-200' : 'bg-gray-50 border-gray-200';
      const iconClass = achievement.completed ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-400';
      const iconName = achievement.completed ? achievement.icon || 'award' : 'lock';
      const textClass = achievement.completed ? 'text-gray-800' : 'text-gray-500';
      
      html += `
        <div class="flex items-start p-3 rounded-lg ${completedClass} border transition-all duration-300 hover:shadow-sm">
          <div class="${iconClass} w-12 h-12 rounded-full flex items-center justify-center mr-4 transition-colors duration-300">
            <i class="fas fa-${iconName}"></i>
          </div>
          <div class="flex-grow">
            <div class="flex justify-between items-start">
              <h4 class="font-medium ${textClass}">${achievement.name}</h4>
              <span class="text-xs font-semibold ${achievement.completed ? 'text-blue-600' : 'text-gray-400'}">+${achievement.points} pts</span>
            </div>
            <p class="text-sm ${achievement.completed ? 'text-gray-600' : 'text-gray-400'}">${achievement.description}</p>
          </div>
        </div>
      `;
    });
    
    container.innerHTML = html;
    console.log(`Rendered ${achievements.length} achievements`);
  }
  
  function renderBadges(badges) {
    const container = document.getElementById('badgesList');
    if (!container) {
      console.warn("Badges container not found");
      return;
    }
    
    // If no badges or empty array, show placeholders
    if (!badges || !badges.length) {
      console.log("No badges data, showing placeholders");
      container.innerHTML = `
        <div class="badge-item flex flex-col items-center p-4 rounded-lg bg-gray-50 border border-gray-200 text-center">
          <div class="bg-gray-200 w-16 h-16 rounded-full flex items-center justify-center mb-2">
            <i class="fas fa-lock text-gray-400"></i>
          </div>
          <h4 class="font-medium text-gray-500 text-sm">Focus Novice</h4>
        </div>
        <div class="badge-item flex flex-col items-center p-4 rounded-lg bg-gray-50 border border-gray-200 text-center">
          <div class="bg-gray-200 w-16 h-16 rounded-full flex items-center justify-center mb-2">
            <i class="fas fa-lock text-gray-400"></i>
          </div>
          <h4 class="font-medium text-gray-500 text-sm">Productivity Champion</h4>
        </div>
      `;
      return;
    }
    
    let html = '';
    
    badges.forEach(badge => {
      const unlockedClass = badge.unlocked ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white' : 'bg-gray-200 text-gray-400';
      const textClass = badge.unlocked ? 'text-gray-800' : 'text-gray-400';
      const borderClass = badge.unlocked ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200';
      const iconName = badge.unlocked ? badge.icon || 'medal' : 'lock';
      
      html += `
        <div class="badge-item flex flex-col items-center p-4 rounded-lg ${borderClass} border text-center transition-all duration-300 hover:shadow-sm">
          <div class="${unlockedClass} w-16 h-16 rounded-full flex items-center justify-center mb-2 transition-colors duration-300">
            <i class="fas fa-${iconName}"></i>
          </div>
          <h4 class="font-medium ${textClass} text-sm">${badge.name}</h4>
        </div>
      `;
    });
    
    container.innerHTML = html;
    console.log(`Rendered ${badges.length} badges`);
  }

    /**
   * Initializes the streak fire effect by monitoring streak elements
   * and adding visual effects based on streak count
   */
  function initStreakFireEffect() {
    const dailyStreakEl = document.getElementById('dailyStreak');
    if (!dailyStreakEl) return;
    
    // Function to update the streak fire effect
    function updateStreakFire() {
      // Extract the streak number from text content
      const streakText = dailyStreakEl.textContent;
      const matches = streakText.match(/(\d+)/);
      
      if (matches && matches[1]) {
        const streakNumber = parseInt(matches[1]);
        
        // Add or remove the fire class based on streak count
        if (!isNaN(streakNumber) && streakNumber >= 3) {
          dailyStreakEl.classList.add('streak-fire');
        } else {
          dailyStreakEl.classList.remove('streak-fire');
        }
      }
    }
    
    // Set up observer to watch for changes to the streak element
    const observer = new MutationObserver(function(mutations) {
      updateStreakFire();
    });
    
    // Observe changes to the streak element
    observer.observe(dailyStreakEl, { 
      characterData: true, 
      childList: true,
      subtree: true
    });
    
    // Initial check when page loads
    updateStreakFire();
  }


  function initialize() {
    console.log("Initializing gamification system...");
    
    // Request gamification status when app loads
    AppState.getSocket().emit('get_gamification_status');
    
    // Check daily login status
    AppState.getSocket().emit('check_daily_status');

    // Initialize streak fire effect
    initStreakFireEffect();
    
    // Set up achievement modal close button
    const achievementModalClose = document.getElementById('achievementModalClose');
    if (achievementModalClose) {
      achievementModalClose.addEventListener('click', closeAchievementModal);
    }
    
    // Initial load of leaderboard (without period selector)
    AppState.getSocket().emit('get_leaderboard_data');
    
    // Request analytics data
    AppState.getSocket().emit('get_analytics_data');
    
    // Add export analytics button handler if it exists
    const exportAnalyticsBtn = document.getElementById('exportAnalyticsBtn');
    if (exportAnalyticsBtn) {
      exportAnalyticsBtn.addEventListener('click', function() {
        AppState.getSocket().emit('export_analytics');
      });
    }
    
    // Set up daily check-in button
    const checkInBtn = document.getElementById('dailyCheckInBtn');
    if (checkInBtn) {
      // Force the button to be visible first
      ensureCheckInButtonVisible();
      
      checkInBtn.addEventListener('click', function() {
        // Disable the button immediately to prevent multiple clicks
        this.disabled = true;
        // Show loading state
        this.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Checking in...';
        
        // Send check-in request to server
        AppState.getSocket().emit('daily_check_in');
      });
    } else {
      console.warn("Daily check-in button not found during initialization");
    }
    
    // Check if already checked in today
    AppState.getSocket().emit('check_daily_status');
    
    // Force data reload before leaving page to save state
    window.addEventListener('beforeunload', function() {
      AppState.getSocket().emit('save_gamification_data');
    });
    
    console.log("Gamification system initialized");
  }
  
  function updateMilestonesProgress(data) {
    // Focus time milestone (1 hour)
    const focusMinutes = data.focus_minutes || 0;
    const focusHourProgress = Math.min(100, (focusMinutes / 60) * 100);
    updateMilestoneBar('milestone1Bar', 'milestone1Progress', focusHourProgress);
    
    // Sessions milestone (5 sessions)
    const sessions = data.sessions || 0;
    const sessionsProgress = Math.min(100, (sessions / 5) * 100);
    updateMilestoneBar('milestone2Bar', 'milestone2Progress', sessionsProgress);
    
    // Pomodoro milestone (10 sessions)
    const pomodoros = data.pomodoro_streak || 0;
    const pomodoroProgress = Math.min(100, (pomodoros / 10) * 100);
    updateMilestoneBar('milestone3Bar', 'milestone3Progress', pomodoroProgress);
  }
  
  function updateMilestoneBar(barId, textId, progress) {
    const bar = document.getElementById(barId);
    const text = document.getElementById(textId);
    
    if (bar) bar.style.width = `${progress}%`;
    if (text) text.textContent = `${Math.round(progress)}%`;
  }
  
  function handleLevelUp(newLevel) {
    // Show level up notification
    Notifications.showRewardNotification({
      title: 'Level Up!',
      message: `Congratulations! You've reached level ${newLevel}!`,
      type: 'level',
      duration: 8000
    });
    
    // Create confetti effect
    Notifications.createConfetti(100);
    
    // Add animation to level badge
    const levelBadge = document.getElementById('userLevel').parentNode;
    levelBadge.classList.add('level-up-animation');
    
    // Remove animation class after it completes
    setTimeout(() => {
      levelBadge.classList.remove('level-up-animation');
    }, 5000);
  }
  
  function updateRecentRewards(reward) {
    const rewardsList = document.getElementById('recentRewardsList');
    if (!rewardsList) return;
    
    // Get current date and time
    const now = new Date();
    const dateStr = now.toLocaleDateString();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Create reward item HTML
    const rewardItem = document.createElement('div');
    rewardItem.className = 'py-3 flex justify-between items-center';
    
    // Set icon and text based on reward type
    let icon, text, pointsText;
    
    switch(reward.type) {
      case 'achievement':
        icon = 'award text-blue-500';
        text = `Achievement Unlocked: ${reward.name}`;
        pointsText = `+${reward.points} pts`;
        break;
      case 'level':
        icon = 'level-up-alt text-green-500';
        text = `Reached Level ${reward.level}`;
        pointsText = '';
        break;
      case 'badge':
        icon = 'shield-alt text-purple-500';
        text = `Badge Earned: ${reward.name}`;
        pointsText = '';
        break;
      case 'streak':
        icon = 'fire text-orange-500';
        text = `${reward.days} Day Streak!`;
        pointsText = `+${reward.points} pts`;
        break;
      case 'session':
        icon = 'check-circle text-blue-500';
        text = 'Completed Focus Session';
        pointsText = `+${reward.points} pts`;
        break;
    }
    
    // Add HTML content
    rewardItem.innerHTML = `
      <div class="flex items-center">
        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
          <i class="fas fa-${icon}"></i>
        </div>
        <div>
          <div class="font-medium text-gray-800">${text}</div>
          <div class="text-xs text-gray-500">${dateStr} at ${timeStr}</div>
        </div>
      </div>
      <div class="text-blue-600 font-medium">${pointsText}</div>
    `;
    
    // Add to the list (at the top)
    if (rewardsList.firstChild) {
      rewardsList.insertBefore(rewardItem, rewardsList.firstChild);
    } else {
      rewardsList.appendChild(rewardItem);
    }
    
    // Remove placeholder if it exists
    const placeholder = rewardsList.querySelector('.text-gray-400');
    if (placeholder) {
      placeholder.remove();
    }
    
    // Limit to 10 most recent rewards
    const items = rewardsList.querySelectorAll('.py-3');
    if (items.length > 10) {
      items[items.length - 1].remove();
    }
  }

  
  // Add these to the Gamification namespace private variables
  let currentLeaderboardPage = 1;
  const usersPerPage = 5;
  let allLeaderboardUsers = [];
  
  // Update the updateLeaderboard function to support pagination
  function updateLeaderboard(users) {
    const leaderboardList = document.getElementById('leaderboardList');
    if (!leaderboardList) return;

    // Store all users for pagination
    if (users && users.length > 0) {
        allLeaderboardUsers = [...users];
        console.log(`Received ${users.length} users for leaderboard`);
    }

    // Clear current items
    leaderboardList.innerHTML = '';

    // If no users, show placeholder
    if (!allLeaderboardUsers || allLeaderboardUsers.length === 0) {
        leaderboardList.innerHTML = `
            <div class="py-3 text-center text-gray-400">
                <i class="fas fa-users opacity-50 text-2xl mb-2"></i>
                <p>No leaderboard data available.</p>
            </div>
        `;
        return;
    }

    // Calculate pagination values
    const totalPages = Math.ceil(allLeaderboardUsers.length / usersPerPage);
    
    // Make sure current page is valid
    if (currentLeaderboardPage > totalPages) {
        currentLeaderboardPage = totalPages;
    } else if (currentLeaderboardPage < 1) {
        currentLeaderboardPage = 1;
    }

    // Calculate indices for the current page
    const startIndex = (currentLeaderboardPage - 1) * usersPerPage;
    const endIndex = Math.min(startIndex + usersPerPage, allLeaderboardUsers.length);
    
    // Get current page users
    const currentPageUsers = allLeaderboardUsers.slice(startIndex, endIndex);
    
    // Check if current user is in the current page
    let currentUserInCurrentPage = currentPageUsers.some(user => user.is_current_user);
    
    // Add leaderboard items for current page
    currentPageUsers.forEach((user, index) => {
        // Determine if this is the current user (for highlighting)
        const isCurrentUser = user.is_current_user === true;
        
        // Calculate actual ranking
        const actualRank = startIndex + index + 1;
        
        // Create leaderboard item with enhanced styling
        const itemEl = document.createElement('div');
        itemEl.className = `leaderboard-item py-3 px-2 flex items-center ${isCurrentUser ? 'current-user' : ''}`;
        
        // Generate rank class for the rank number
        const rankClass = actualRank <= 3 ? `rank-${actualRank}` : 'bg-blue-100 text-blue-600';
        
        // Generate avatar initials
        const nameParts = user.name.split(' ');
        let initials = '';
        
        if (nameParts.length === 1) {
            // Single name - take first two letters
            initials = nameParts[0].substring(0, 2).toUpperCase();
        } else {
            // Multiple names - take first letter of first and first letter of last
            initials = (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase();
        }
        
        // Generate avatar background color using reliable base colors
        const colorIndex = user.id % 8; // Use 8 well-supported colors
        const colors = [
            'bg-blue-200',   // Light blue
            'bg-red-200',    // Light red
            'bg-green-200',  // Light green
            'bg-purple-200', // Light purple
            'bg-yellow-200', // Light yellow
            'bg-indigo-200', // Light indigo
            'bg-pink-200',   // Light pink
            'bg-teal-200'    // Light teal
        ];
        const avatarBgColor = colors[colorIndex];
        
        // Build HTML with enhanced current user indicator
        itemEl.innerHTML = `
            <div class="leaderboard-rank ${rankClass} mr-4">${actualRank}</div>
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-gray-800 font-medium mr-3" 
                 style="background-color: ${getColorFromClass(avatarBgColor)};">
                ${initials}
            </div>
            <div class="flex-grow">
                <div class="font-medium text-gray-800">${user.name} ${isCurrentUser ? '<span class="text-xs text-blue-600 ml-1">(You)</span>' : ''}</div>
                <div class="text-xs text-gray-500">Level ${user.level}</div>
            </div>
            <div class="font-semibold text-blue-600">${user.points.toLocaleString()} pts</div>
        `;
        
        // If this is the current user, scroll to it after rendering
        if (isCurrentUser) {
            itemEl.setAttribute('id', 'current-user-item');
            
            // Add a slight delay to ensure the DOM is updated
            setTimeout(() => {
                itemEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        }
        
        leaderboardList.appendChild(itemEl);
    });
    
    // If current user is not in the current page but exists in the data, add pagination hint
    if (!currentUserInCurrentPage) {
        const currentUserInFullList = allLeaderboardUsers.findIndex(user => user.is_current_user);
        if (currentUserInFullList !== -1) {
            const userPage = Math.floor(currentUserInFullList / usersPerPage) + 1;
            
            const userPageHint = document.createElement('div');
            userPageHint.className = 'text-center text-sm text-blue-600 mt-2 mb-1';
            userPageHint.innerHTML = `<i class="fas fa-info-circle mr-1"></i> You are on page ${userPage} of the leaderboard`;
            leaderboardList.appendChild(userPageHint);
        }
    }
    
    // Add pagination controls
    if (totalPages > 1) {
        const paginationContainer = document.createElement('div');
        paginationContainer.className = 'flex justify-center items-center mt-4 space-x-2';
        
        // Previous page button
        const prevButton = document.createElement('button');
        prevButton.className = 'px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors duration-200 ' + 
                                (currentLeaderboardPage === 1 ? 'opacity-50 cursor-not-allowed' : '');
        prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevButton.disabled = currentLeaderboardPage === 1;
        prevButton.addEventListener('click', () => {
            if (currentLeaderboardPage > 1) {
                currentLeaderboardPage--;
                updateLeaderboard();
            }
        });
        paginationContainer.appendChild(prevButton);
        
        // Page numbers
        const pageInfo = document.createElement('span');
        pageInfo.className = 'text-sm text-gray-600 mx-2';
        pageInfo.textContent = `Page ${currentLeaderboardPage} of ${totalPages}`;
        paginationContainer.appendChild(pageInfo);
        
        // Next page button
        const nextButton = document.createElement('button');
        nextButton.className = 'px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors duration-200 ' + 
                                (currentLeaderboardPage === totalPages ? 'opacity-50 cursor-not-allowed' : '');
        nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextButton.disabled = currentLeaderboardPage === totalPages;
        nextButton.addEventListener('click', () => {
            if (currentLeaderboardPage < totalPages) {
                currentLeaderboardPage++;
                updateLeaderboard();
            }
        });
        paginationContainer.appendChild(nextButton);
        
        leaderboardList.appendChild(paginationContainer);
    }
  }

  // Helper function to convert Tailwind classes to actual color values
  function getColorFromClass(className) {
      const colorMap = {
          'bg-blue-200': '#BFDBFE',   // Light blue
          'bg-red-200': '#FECACA',    // Light red
          'bg-green-200': '#A7F3D0',  // Light green
          'bg-purple-200': '#DDD6FE', // Light purple
          'bg-yellow-200': '#FEF08A', // Light yellow
          'bg-indigo-200': '#C7D2FE', // Light indigo
          'bg-pink-200': '#FBCFE8',   // Light pink
          'bg-teal-200': '#99F6E4'    // Light teal
      };
      return colorMap[className] || '#E5E7EB'; // Default to gray-200 if not found
  }
  
  function processNewAchievements(achievements, points) {
    if (!achievements || achievements.length === 0) {
      // Just show points if there are any
      if (points && points.total_points > 0) {
        Notifications.showPointsAnimation(points.total_points);
      }
      return;
    }
    
    // Add short delay before showing achievements
    let delay = 500;
    
    // First show points if there are any
    if (points && points.total_points > 0) {
      Notifications.showPointsAnimation(points.total_points);
    }
    
    // Process level up first if there was one
    if (points && points.level_up) {
      setTimeout(() => {
        handleLevelUp(points.new_level);
      }, delay);
      delay += 5500;  // Add 5.5s delay for the modal to be shown and auto-closed
    }
    
    // Then show each achievement with a delay between them
    achievements.forEach(achievement => {
      setTimeout(() => {
        // Show achievement notification
        if (achievement.type === 'achievement') {
          Notifications.showRewardNotification({
            title: 'Achievement Unlocked!',
            message: achievement.description,
            points: achievement.points,
            type: 'achievement'
          });
        } else if (achievement.type === 'badge') {
          Notifications.showRewardNotification({
            title: 'Badge Earned!',
            message: achievement.description,
            type: 'badge'
          });
        }
        
        // Add to recent rewards
        updateRecentRewards(achievement);
        
      }, delay);
      
      delay += 3000;  // Space out notifications
    });
  }
  
  function processSessionCompletion(sessionData) {
    // Extract points and achievements from session data
    const points = sessionData.points;
    const achievements = sessionData.achievements || [];
    
    // Delay before showing notifications to ensure UI is updated
    setTimeout(() => {
      // Show point notification if points were earned
      if (points && points.total_points > 0) {
        Notifications.showRewardNotification({
          title: 'Session Complete!',
          message: 'You earned points for your focus time.',
          points: points.total_points,
          type: 'points'
        });
        
        // Add to recent rewards
        updateRecentRewards({
          type: 'session',
          points: points.total_points
        });
      }
      
      // If user leveled up, show level up notification and add confetti
      if (points && points.level_up) {
        setTimeout(() => {
          handleLevelUp(points.new_level);
        }, 2000);
      }
      
      // Process achievements with delays between them
      let achievementDelay = points && points.total_points > 0 ? 3000 : 1000;
      
      achievements.forEach(achievement => {
        setTimeout(() => {
          // Show achievement notification
          if (achievement.type === 'achievement') {
            Notifications.showRewardNotification({
              title: 'Achievement Unlocked!',
              message: achievement.description,
              points: achievement.points,
              type: 'achievement'
            });
          } else if (achievement.type === 'badge') {
            Notifications.showRewardNotification({
              title: 'Badge Earned!',
              message: achievement.description,
              type: 'badge'
            });
          }
          
          // Add to recent rewards
          updateRecentRewards(achievement);
          
        }, achievementDelay);
        
        achievementDelay += 3000;  // Space out notifications
      });
      
    }, 1000);
  }
  
  function closeAchievementModal() {
    const modal = document.getElementById('achievementModal');
    if (modal) modal.classList.add('hidden');
    
    // If it was hiding points element, show it again for next achievement
    const pointsContainer = document.getElementById('achievementModalPoints');
    if (pointsContainer) {
      const container = pointsContainer.parentElement.parentElement;
      if (container) container.classList.remove('hidden');
    }
  }

  function handleDailyStatusCheck(data) {
    const checkInBtn = document.getElementById('dailyCheckInBtn');
    const checkInStatus = document.getElementById('checkInStatus');
    
    if (checkInBtn) {
        // First ensure the button is visible regardless of state
        checkInBtn.style.display = 'flex';
        checkInBtn.style.opacity = '1';
        checkInBtn.style.visibility = 'visible';
        
        if (data.already_checked_in) {
            // Disable button and change style instead of hiding it
            checkInBtn.disabled = true;
            checkInBtn.classList.add('bg-gray-500');
            checkInBtn.classList.remove('bg-orange-500', 'hover:bg-orange-600');
            
            // Show the status message
            if (checkInStatus) {
                checkInStatus.classList.remove('hidden');
            }
        } else {
            // Make sure button is enabled and has correct styling
            checkInBtn.disabled = false;
            checkInBtn.classList.add('bg-orange-500', 'hover:bg-orange-600');
            checkInBtn.classList.remove('bg-gray-500');
            
            // Hide the status message
            if (checkInStatus) {
                checkInStatus.classList.add('hidden');
            }
        }
        
        // If the server sent the current streak, update it
        if (data.current_streak !== undefined) {
            const dailyStreakEl = document.getElementById('dailyStreak');
            if (dailyStreakEl) {
                const streak = data.current_streak;
                dailyStreakEl.textContent = `${streak} day${streak !== 1 ? 's' : ''}`;
            }
        }
    } else {
        console.warn("Daily check-in button not found in DOM");
    }
  }

  function handleDailyCheckInResponse(data) {
    const checkInBtn = document.getElementById('dailyCheckInBtn');
    const checkInStatus = document.getElementById('checkInStatus');
    
    if (checkInBtn) {
        // Reset button state
        checkInBtn.innerHTML = '<i class="fas fa-calendar-check mr-2"></i>Check In Today';
        
        if (data.success) {
            // Show success notification with TOTAL points
            Notifications.showRewardNotification({
                title: 'Daily Streak!',
                message: `You've checked in for ${data.streak} days in a row!`,
                points: data.points_earned, // This now contains the TOTAL points (base + streak bonus)
                type: 'streak'
            });
            
            // Update streaks display immediately without waiting for server
            const dailyStreakEl = document.getElementById('dailyStreak');
            if (dailyStreakEl) {
                const streak = data.streak || 0;
                dailyStreakEl.textContent = `${streak} day${streak !== 1 ? 's' : ''}`;
                
                // Add a quick highlight animation to the streak display
                dailyStreakEl.classList.add('streak-highlight');
                setTimeout(() => {
                    dailyStreakEl.classList.remove('streak-highlight');
                }, 2000);
            }
            
            // Log the streak change to help debugging
            console.log(`Streak updated: ${data.previous_streak || 0} -> ${data.streak || 0}, total points: ${data.points_earned}`);
            
            // Disable button and show already checked in message
            // BUT KEEP THE BUTTON VISIBLE
            checkInBtn.disabled = true;
            checkInBtn.classList.add('bg-gray-500');
            checkInBtn.classList.remove('bg-orange-500', 'hover:bg-orange-600');
            checkInBtn.style.display = 'flex'; // Force display
            
            if (checkInStatus) {
                checkInStatus.classList.remove('hidden');
            }
            
            // Process any achievements
            if (data.achievements && data.achievements.length > 0) {
                setTimeout(() => {
                    Gamification.processNewAchievements(data.achievements);
                }, 2000);
            }
            
            // Request updated gamification status
            AppState.getSocket().emit('get_gamification_status');
        } else {
            // Show error message
            Notifications.showNotification(data.message || 'Something went wrong. Please try again.', 'error');
            checkInBtn.disabled = false;
        }
    }
  }

  function saveGamificationState() {
    console.log("Saving gamification state...");
    AppState.getSocket().emit('save_gamification_data');
  }

  // Public methods
  return {
    initialize: initialize,
    updateGamificationUI: updateGamificationUI,
    updateLeaderboard: updateLeaderboard,
    processNewAchievements: processNewAchievements,
    processSessionCompletion: processSessionCompletion,

    // Daily check-in methods
    handleDailyCheckInResponse: handleDailyCheckInResponse,
    handleDailyStatusCheck: handleDailyStatusCheck,
    
    // New methods for visibility and state management
    renderAchievements: renderAchievements,
    renderBadges: renderBadges,
    ensureCheckInButtonVisible: ensureCheckInButtonVisible,
    saveGamificationState: saveGamificationState,
    
    handleLoginStreakUpdate: function(data) {
      if (data.error) {
        console.error("Error updating login streak:", data.error);
        return;
      }
      
      // Process any achievements from login streak
      if (data.achievements && data.achievements.length > 0) {
        processNewAchievements(data.achievements);
      }
      
      // Show notification if there was a streak continuation or reset
      if (data.streak_info.streak_continued) {
        Notifications.showRewardNotification({
          title: 'Daily Streak!',
          message: `You've used FocusGuard for ${data.streak_info.streak} days in a row!`,
          type: 'streak'
        });
      } else if (data.streak_info.streak_reset) {
        Notifications.showNotification('Welcome back! Your daily streak has been reset.', 'info');
      } else if (data.streak_info.new_day) {
        Notifications.showNotification('Welcome to FocusGuard!', 'info');
      }
    },

    resetLeaderboardPage: function() {
      currentLeaderboardPage = 1;
    },
    
    nextLeaderboardPage: function() {
      if (allLeaderboardUsers.length > (currentLeaderboardPage * usersPerPage)) {
        currentLeaderboardPage++;
        updateLeaderboard();
      }
    },
    
    prevLeaderboardPage: function() {
      if (currentLeaderboardPage > 1) {
        currentLeaderboardPage--;
        updateLeaderboard();
      }
    }
  };
})();

// Export the Gamification namespace
window.Gamification = Gamification;