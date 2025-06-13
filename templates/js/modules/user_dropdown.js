/**
 * user_dropdown.js
 * Handles user dropdown menu functionality
 */

// Wait for DOM to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
  // Initialize user dropdown functionality
  initUserDropdown();
});

function initUserDropdown() {
  const dropdownButton = document.getElementById("userDropdownButton");
  const dropdownMenu = document.getElementById("userDropdownMenu");

  // Check if dropdown elements exist
  if (!dropdownButton || !dropdownMenu) {
    console.error("User dropdown elements not found:", {
      button: dropdownButton,
      menu: dropdownMenu,
    });
    return;
  }

  // Toggle dropdown when button is clicked
  dropdownButton.addEventListener("click", (event) => {
    event.stopPropagation();
    event.preventDefault();
    dropdownMenu.classList.toggle("active");
    console.log("Dropdown menu toggled:", dropdownMenu.classList.contains("active"));
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (event) => {
    if (
      dropdownMenu.classList.contains("active") &&
      !dropdownButton.contains(event.target) &&
      !dropdownMenu.contains(event.target)
    ) {
      dropdownMenu.classList.remove("active");
      console.log("Dropdown menu closed by outside click");
    }
  });
  
  // Add detection warning to navigation links in dropdown
  setupNavigationWarnings();
}

/**
 * Sets up warning dialogs for navigation links in the dropdown menu
 * when detection is active
 */
function setupNavigationWarnings() {
  // Profile link
  const profileLink = document.querySelector('#userDropdownMenu a[href="/profile"]');
  if (profileLink) {
    profileLink.addEventListener('click', function(e) {
      // Check if detection is running
      if (typeof AppState !== 'undefined' && AppState.isDetecting()) {
        e.preventDefault();
        
        const confirmed = confirm('Detection is still running. Are you sure you want to go to profile page? Your session will be stopped.');
        
        if (confirmed) {
          // Stop detection if user confirms
          if (typeof Detection !== 'undefined' && Detection.stopDetection) {
            Detection.stopDetection();
            
            // Wait briefly for detection to stop before navigating
            setTimeout(() => {
              window.location.href = '/profile';
            }, 500);
          } else {
            // If Detection module unavailable, just navigate
            window.location.href = '/profile';
          }
        }
      }
    });
  }
  
  // Settings link (handled differently since it's a tab, not a page navigation)
  const settingsLink = document.querySelector('#userDropdownMenu a[href="#"][onclick*="settingsTab"]');
  if (settingsLink) {
    // We don't need to stop detection when switching to settings tab,
    // so we don't add a special handler here
  }
  
  // Logout link
  const logoutLink = document.querySelector('#userDropdownMenu a[href="/logout"]');
  if (logoutLink) {
    logoutLink.addEventListener('click', function(e) {
      // Check if detection is running
      if (typeof AppState !== 'undefined' && AppState.isDetecting()) {
        e.preventDefault();
        
        const confirmed = confirm('Detection is still running. Are you sure you want to logout? Your session will be stopped.');
        
        if (confirmed) {
          // Stop detection if user confirms
          if (typeof Detection !== 'undefined' && Detection.stopDetection) {
            Detection.stopDetection();
            
            // Wait briefly for detection to stop before logging out
            setTimeout(() => {
              window.location.href = '/logout';
            }, 500);
          } else {
            // If Detection module unavailable, just navigate
            window.location.href = '/logout';
          }
        }
      }
    });
  }
}