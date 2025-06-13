/**
 * auth.js
 * Handles authentication functionality for FocusGuard application
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize UI utilities if available
  if (typeof UIUtils !== 'undefined' && UIUtils.setupAlertStyles) {
    UIUtils.setupAlertStyles();
  }
  
  // Setup form handlers
  setupLoginForm();
  setupRegistrationForm();
  
  // Setup password toggle functionality
  setupPasswordToggles();
  
  console.log("Authentication module initialized");
});

/**
 * Sets up password visibility toggle buttons
 */
function setupPasswordToggles() {
  // For registration page
  const passwordToggle = document.getElementById("passwordToggle");
  const confirmPasswordToggle = document.getElementById("confirmPasswordToggle");
  const passwordField = document.getElementById("password");
  const confirmPasswordField = document.getElementById("confirmPassword");
  
  // Setup password toggle
  if (passwordToggle && passwordField) {
    passwordToggle.addEventListener("click", () => {
      // Toggle password visibility
      const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
      passwordField.setAttribute("type", type);
      
      // Toggle icon
      const icon = passwordToggle.querySelector("i");
      if (type === "password") {
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
        passwordToggle.setAttribute("title", "Show Password");
      } else {
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
        passwordToggle.setAttribute("title", "Hide Password");
      }
    });
  }
  
  // Setup confirm password toggle
  if (confirmPasswordToggle && confirmPasswordField) {
    confirmPasswordToggle.addEventListener("click", () => {
      // Toggle password visibility
      const type = confirmPasswordField.getAttribute("type") === "password" ? "text" : "password";
      confirmPasswordField.setAttribute("type", type);
      
      // Toggle icon
      const icon = confirmPasswordToggle.querySelector("i");
      if (type === "password") {
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
        confirmPasswordToggle.setAttribute("title", "Show Password");
      } else {
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
        confirmPasswordToggle.setAttribute("title", "Hide Password");
      }
    });
  }
  
  // For login page
  const loginPasswordToggle = document.getElementById("loginPasswordToggle");
  const loginPasswordField = document.getElementById("password");
  
  if (loginPasswordToggle && loginPasswordField) {
    loginPasswordToggle.addEventListener("click", () => {
      // Toggle password visibility
      const type = loginPasswordField.getAttribute("type") === "password" ? "text" : "password";
      loginPasswordField.setAttribute("type", type);
      
      // Toggle icon
      const icon = loginPasswordToggle.querySelector("i");
      if (type === "password") {
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
        loginPasswordToggle.setAttribute("title", "Show Password");
      } else {
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
        loginPasswordToggle.setAttribute("title", "Hide Password");
      }
    });
  }
}

/**
 * Sets up the login form with validation and submission handling
 */
function setupLoginForm() {
  const loginForm = document.getElementById("loginForm");
  
  if (!loginForm) return; // Not on login page
  
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    // Get form inputs
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember").checked;
    
    // Basic validation
    if (!username || !password) {
      showAlert("loginAlert", "Please enter both username and password.", "error");
      return;
    }
    
    // Prepare data for submission
    const formData = {
      username,
      password,
      remember
    };
    
    try {
      // Display loading state
      const submitButton = loginForm.querySelector("button[type='submit']");
      const originalText = submitButton.innerHTML;
      submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...';
      submitButton.disabled = true;
      
      // Send login request
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Login successful
        showAlert("loginAlert", "Login successful! Redirecting...", "success");
        
        // Redirect to main page after short delay
        setTimeout(() => {
          window.location.href = "/";
        }, 1000);
      } else {
        // Login failed
        showAlert("loginAlert", data.message || "Login failed. Please check your credentials.", "error");
        
        // Reset submit button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
      }
    } catch (error) {
      console.error("Login error:", error);
      showAlert("loginAlert", "An error occurred. Please try again later.", "error");
      
      // Reset submit button
      const submitButton = loginForm.querySelector("button[type='submit']");
      submitButton.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Login';
      submitButton.disabled = false;
    }
  });
}

/**
 * Sets up the registration form with validation and submission handling
 */
function setupRegistrationForm() {
  const registerForm = document.getElementById("registerForm");
  
  if (!registerForm) return; // Not on registration page
  
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    // Get form inputs
    const fullName = document.getElementById("fullName").value.trim();
    const email = document.getElementById("email").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const terms = document.getElementById("terms").checked;
    
    // Validation
    if (!fullName || !email || !username || !password || !confirmPassword) {
      showAlert("registerAlert", "Please fill in all fields.", "error");
      return;
    }
    
    if (!validateEmail(email)) {
      showAlert("registerAlert", "Please enter a valid email address.", "error");
      return;
    }
    
    if (password.length < 8) {
      showAlert("registerAlert", "Password must be at least 8 characters long.", "error");
      return;
    }
    
    if (password !== confirmPassword) {
      showAlert("registerAlert", "Passwords do not match.", "error");
      return;
    }
    
    if (!terms) {
      showAlert("registerAlert", "You must agree to the Terms of Service and Privacy Policy.", "error");
      return;
    }
    
    // Prepare data for submission
    const formData = {
      fullName,
      email,
      username,
      password
    };
    
    try {
      // Display loading state
      const submitButton = registerForm.querySelector("button[type='submit']");
      const originalText = submitButton.innerHTML;
      submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating Account...';
      submitButton.disabled = true;
      
      // Send registration request
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Registration successful
        showAlert("registerAlert", "Account created successfully! Redirecting to login...", "success");
        
        // Redirect to login page after short delay
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
      } else {
        // Registration failed
        showAlert("registerAlert", data.message || "Registration failed. Please try again.", "error");
        
        // Reset submit button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
      }
    } catch (error) {
      console.error("Registration error:", error);
      showAlert("registerAlert", "An error occurred. Please try again later.", "error");
      
      // Reset submit button
      const submitButton = registerForm.querySelector("button[type='submit']");
      submitButton.innerHTML = '<i class="fas fa-user-plus mr-2"></i>Create Account';
      submitButton.disabled = false;
    }
  });
}

/**
 * Shows an alert message in the specified container
 * @param {string} alertId - ID of the alert container
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, error, warning, info)
 */
function showAlert(alertId, message, type = "info") {
  const alertElement = document.getElementById(alertId);
  const messageElement = document.getElementById(`${alertId}Message`);
  
  if (!alertElement || !messageElement) return;
  
  // Set message
  messageElement.textContent = message;
  
  // Reset classes
  alertElement.className = "mb-4 px-4 py-3 rounded relative";
  
  // Apply appropriate styling based on type
  switch (type) {
    case "success":
      alertElement.classList.add("bg-green-100", "border", "border-green-400", "text-green-700");
      messageElement.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
      break;
    case "error":
      alertElement.classList.add("bg-red-100", "border", "border-red-400", "text-red-700");
      messageElement.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
      break;
    case "warning":
      alertElement.classList.add("bg-yellow-100", "border", "border-yellow-400", "text-yellow-700");
      messageElement.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${message}`;
      break;
    default: // info
      alertElement.classList.add("bg-blue-100", "border", "border-blue-400", "text-blue-700");
      messageElement.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${message}`;
  }
  
  // Show the alert
  alertElement.classList.remove("hidden");
  
  // Optionally use notification system if available
  if (typeof Notifications !== 'undefined' && Notifications.showNotification) {
    Notifications.showNotification(message, type);
  }
  
  // Auto-hide success messages after 5 seconds
  if (type === "success") {
    setTimeout(() => {
      alertElement.classList.add("hidden");
    }, 5000);
  }
}

/**
 * Validates an email address
 * @param {string} email - Email address to validate
 * @returns {boolean} - True if email is valid, false otherwise
 */
function validateEmail(email) {
  const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}