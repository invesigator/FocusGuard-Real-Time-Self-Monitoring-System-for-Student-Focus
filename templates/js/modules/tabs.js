/**
 * tabs.js
 * Handles tab navigation functionality with persistence across page refreshes
 */

const Tabs = (function() {
  // Private methods
  function setupTabClickHandlers() {
    const tabs = document.querySelectorAll(".tab-btn");
    
    // First ensure all tab content is hidden except the first one
    document.querySelectorAll(".tab-content").forEach((content, index) => {
      if (index === 0) {
        content.classList.add("active");
      } else {
        content.classList.remove("active");
      }
    });
    
    // Add click event listeners to tabs
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const tabContentId = tab.getAttribute("data-tab");
        console.log("Tab clicked:", tabContentId);
        
        // Remove active class from all tabs
        tabs.forEach((t) => {
          t.classList.remove("border-blue-600", "text-blue-600");
          t.classList.add("text-gray-500", "hover:text-gray-700");
        });

        // Add active class to clicked tab
        tab.classList.remove("text-gray-500", "hover:text-gray-700");
        tab.classList.add("border-blue-600", "text-blue-600");

        // Show the corresponding content
        document.querySelectorAll(".tab-content").forEach((content) => {
          content.classList.remove("active");
        });
        
        const targetContent = document.getElementById(tabContentId);
        if (targetContent) {
          targetContent.classList.add("active");
          
          // Handle special actions for specific tabs
          if (tabContentId === "pomodoro-section") {
            Pomodoro.updateTimerDisplay();
          } else if (tabContentId === "analytics-section") {
            // Request fresh analytics data when switching to analytics tab
            AppState.getSocket().emit('load_analytics_tab');
          }
          
          // Save the active tab to localStorage for persistence
          localStorage.setItem('focusguard_active_tab', tabContentId);
        } else {
          console.error("Tab content not found:", tabContentId);
        }
      });
    });
    
    console.log("Tab setup completed");
  }
  
  // Function to restore the previously active tab
  function restoreSavedTab() {
    // Check if there's a saved tab in localStorage
    const savedTabId = localStorage.getItem('focusguard_active_tab');
    
    if (savedTabId) {
      // Find the tab button for the saved tab
      const tabButton = document.querySelector(`.tab-btn[data-tab="${savedTabId}"]`);
      
      // If the button exists, switch to that tab
      if (tabButton) {
        console.log(`Restoring saved tab: ${savedTabId}`);
        tabButton.click();
      }
    }
  }

  // Public methods
  return {
    initialize: function() {
      setupTabClickHandlers();
      // After setting up the tabs, restore the previously active tab
      setTimeout(restoreSavedTab, 100); // Small delay to ensure DOM is fully ready
    },
    
    switchToTab: function(tabId) {
      const tabButton = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
      if (tabButton) {
        tabButton.click();
      }
    }
  };
})();

// Export the Tabs namespace
window.Tabs = Tabs;