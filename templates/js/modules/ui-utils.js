/**
 * ui-utils.js
 * Common UI utility functions
 */

const UIUtils = (function() {
  // Private methods
  function setupAlertStyles() {
    // Apply enhanced styling to alerts
    document.querySelectorAll('#alertsContainer > div').forEach(el => {
      el.classList.add('alert-box');
    });
    
    // Apply button effects to all action buttons
    document.querySelectorAll('button.px-6.py-2').forEach(btn => {
      btn.classList.add('btn-focus-effect');
    });
    
    // Add placeholder animation
    const placeholderIcon = document.querySelector('#placeholderFeed i');
    if (placeholderIcon) {
      placeholderIcon.classList.add('placeholder-pulse');
    }
  }

  // Public methods
  return {
    setupAlertStyles: setupAlertStyles
  };
})();

// Export the UIUtils namespace
window.UIUtils = UIUtils;