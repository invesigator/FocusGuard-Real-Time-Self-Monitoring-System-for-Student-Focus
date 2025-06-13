// Add this to your main.js or create a new user-menu.js file
document.addEventListener('DOMContentLoaded', () => {
  // User menu dropdown
  const userMenuButton = document.getElementById('userMenuButton');
  const userMenuDropdown = document.getElementById('userMenuDropdown');
  const usernameDisplay = document.getElementById('usernameDisplay');
  
  // Display username from localStorage
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (user.username) {
      usernameDisplay.textContent = user.username;
  }
  
  // Toggle dropdown
  userMenuButton.addEventListener('click', () => {
      userMenuDropdown.classList.toggle('hidden');
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', (event) => {
      if (!userMenuButton.contains(event.target) && !userMenuDropdown.contains(event.target)) {
          userMenuDropdown.classList.add('hidden');
      }
  });
});