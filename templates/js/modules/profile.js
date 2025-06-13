// Add this code to profile.js or create a new file if needed
document.addEventListener("DOMContentLoaded", function () {
  // Existing profile edit modal logic
  const editProfileModal = document.getElementById("editProfileModal");
  const showEditProfileModal = document.getElementById("showEditProfileModal");
  const cancelProfileBtn = document.getElementById("cancelProfileBtn");
  const saveProfileBtn = document.getElementById("saveProfileBtn");
  const editProfileForm = document.getElementById("editProfileForm");

  // Show modal
  if (showEditProfileModal) {
    showEditProfileModal.addEventListener("click", function () {
      editProfileModal.classList.remove("hidden");
    });
  }

  // Hide modal
  if (cancelProfileBtn) {
    cancelProfileBtn.addEventListener("click", function () {
      editProfileModal.classList.add("hidden");
    });
  }

  // Close modal when clicking outside
  if (editProfileModal) {
    editProfileModal.addEventListener("click", function (e) {
      if (e.target === editProfileModal) {
        editProfileModal.classList.add("hidden");
      }
    });
  }

  // Handle profile form submission (existing code)
  if (saveProfileBtn) {
    saveProfileBtn.addEventListener("click", async function () {
      // Existing profile save logic...
    });
  }

  // =========================================================
  // NEW CODE FOR VIEW ALL SESSIONS FUNCTIONALITY
  // =========================================================
  
  // Get the View All link
  const viewAllLink = document.querySelector('a[href="#"].view-all-sessions');
  // Get the sessions modal
  const sessionsModal = document.getElementById("allSessionsModal");
  // Get the close button
  const closeSessionsBtn = document.getElementById("closeSessionsModalBtn");
  
  // Variables for pagination
  let allSessions = [];
  let currentPage = 1;
  const sessionsPerPage = 10;
  
  // Add event listener to View All link
  if (viewAllLink) {
    viewAllLink.addEventListener("click", function (e) {
      e.preventDefault();
      fetchAllSessions();
      sessionsModal.classList.remove("hidden");
    });
  }
  
  // Close modal when clicking close button
  if (closeSessionsBtn) {
    closeSessionsBtn.addEventListener("click", function () {
      sessionsModal.classList.add("hidden");
    });
  }
  
  // Close modal when clicking outside
  if (sessionsModal) {
    sessionsModal.addEventListener("click", function (e) {
      if (e.target === sessionsModal) {
        sessionsModal.classList.add("hidden");
      }
    });
  }
  
  // Fetch all sessions from the API
  async function fetchAllSessions() {
    try {
      const loadingIndicator = document.getElementById("sessionsLoadingIndicator");
      const errorMessage = document.getElementById("sessionsErrorMessage");
      
      if (loadingIndicator) loadingIndicator.classList.remove("hidden");
      if (errorMessage) errorMessage.classList.add("hidden");
      
      // Try the new dedicated endpoint first
      let response = await fetch("/api/user/sessions/all");
      let data = await response.json();
      
      // If the endpoint doesn't exist (404), fall back to the original endpoint with limit
      if (!response.ok && response.status === 404) {
        console.log("Falling back to original sessions endpoint");
        response = await fetch("/api/user/sessions?limit=100");
        data = await response.json();
      }
      
      if (loadingIndicator) loadingIndicator.classList.add("hidden");
      
      if (data.success) {
        allSessions = data.sessions;
        currentPage = 1;
        renderSessionsTable();
        updatePagination();
      } else {
        if (errorMessage) {
          errorMessage.textContent = data.message || "Failed to load sessions";
          errorMessage.classList.remove("hidden");
        }
      }
    } catch (error) {
      console.error("Error fetching sessions:", error);
      if (loadingIndicator) loadingIndicator.classList.add("hidden");
      if (errorMessage) {
        errorMessage.textContent = "An error occurred while loading your sessions";
        errorMessage.classList.remove("hidden");
      }
    }
  }
  
  // Render the sessions table with the current page of data
  function renderSessionsTable() {
    const tableBody = document.getElementById("allSessionsTableBody");
    if (!tableBody) return;
    
    // Calculate start and end indices
    const startIndex = (currentPage - 1) * sessionsPerPage;
    const endIndex = Math.min(startIndex + sessionsPerPage, allSessions.length);
    
    // Clear the table
    tableBody.innerHTML = "";
    
    // If no sessions
    if (allSessions.length === 0) {
      const emptyRow = document.createElement("tr");
      emptyRow.innerHTML = `
        <td colspan="6" class="px-4 py-8 text-center text-gray-500">
          No session history available
        </td>
      `;
      tableBody.appendChild(emptyRow);
      return;
    }
    
    // Add session rows
    for (let i = startIndex; i < endIndex; i++) {
      const session = allSessions[i];
      
      // Format the date
      let dateDisplay = session.start_time;
      if (typeof session.start_time === 'string') {
        // Try to parse and format the date
        try {
          const date = new Date(session.start_time);
          
          // Format date as "Apr 19, 2025 11:54 PM" to match the UI in the screenshot
          const options = { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric',
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true
          };
          dateDisplay = date.toLocaleDateString('en-US', options);
        } catch (e) {
          console.warn("Could not parse date:", session.start_time);
        }
      }
      
      const row = document.createElement("tr");
      row.className = "hover:bg-gray-50";
      row.innerHTML = `
        <td class="px-4 py-4 whitespace-nowrap">${dateDisplay}</td>
        <td class="px-4 py-4 whitespace-nowrap">${session.duration_minutes} min</td>
        <td class="px-4 py-4 whitespace-nowrap">
          <div class="flex space-x-2">
            <span class="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800" title="Drowsy Events">
              <i class="fas fa-eye-slash text-xs mr-1"></i>${session.drowsy_events}
            </span>
            <span class="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800" title="Yawn Events">
              <i class="fas fa-wind text-xs mr-1"></i>${session.yawn_events}
            </span>
            <span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800" title="Distraction Events">
              <i class="fas fa-arrows-up-down-left-right text-xs mr-1"></i>${session.distraction_events}
            </span>
          </div>
        </td>
        <td class="px-4 py-4 whitespace-nowrap">${session.completed_pomodoros || 0}</td>
        <td class="px-4 py-4 whitespace-nowrap text-blue-600 font-medium">+${session.points_earned || 0}</td>
      `;
      
      tableBody.appendChild(row);
    }
  }
  
  // Update pagination controls
  function updatePagination() {
    const paginationContainer = document.getElementById("sessionsPaginationControls");
    if (!paginationContainer) return;
    
    // Calculate total pages
    const totalPages = Math.ceil(allSessions.length / sessionsPerPage);
    
    // Don't show pagination if there's only one page
    if (totalPages <= 1) {
      paginationContainer.classList.add("hidden");
      return;
    }
    
    paginationContainer.classList.remove("hidden");
    
    // Generate pagination HTML
    let paginationHTML = `
      <div class="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
        <div class="flex-1 flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Showing <span class="font-medium">${Math.min(allSessions.length, 1 + (currentPage - 1) * sessionsPerPage)}</span>
              to <span class="font-medium">${Math.min(allSessions.length, currentPage * sessionsPerPage)}</span>
              of <span class="font-medium">${allSessions.length}</span> results
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
              <!-- Previous button -->
              <button
                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${currentPage === 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}" 
                ${currentPage === 1 ? 'disabled' : ''}
                id="prevPageBtn">
                <span class="sr-only">Previous</span>
                <i class="fas fa-chevron-left"></i>
              </button>
              
              <!-- Page number -->
              <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                Page ${currentPage} of ${totalPages}
              </span>
              
              <!-- Next button -->
              <button
                class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${currentPage === totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}" 
                ${currentPage === totalPages ? 'disabled' : ''}
                id="nextPageBtn">
                <span class="sr-only">Next</span>
                <i class="fas fa-chevron-right"></i>
              </button>
            </nav>
          </div>
        </div>
      </div>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
    
    // Add event listeners to pagination buttons
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");
    
    if (prevBtn && currentPage > 1) {
      prevBtn.addEventListener("click", function() {
        if (currentPage > 1) {
          currentPage--;
          renderSessionsTable();
          updatePagination();
        }
      });
    }
    
    if (nextBtn && currentPage < totalPages) {
      nextBtn.addEventListener("click", function() {
        if (currentPage < totalPages) {
          currentPage++;
          renderSessionsTable();
          updatePagination();
        }
      });
    }
  }
  
  // Expose these functions for potential external use
  window.sessionsView = {
    fetchAllSessions,
    renderSessionsTable,
    updatePagination,
    nextPage: function() {
      if (currentPage < Math.ceil(allSessions.length / sessionsPerPage)) {
        currentPage++;
        renderSessionsTable();
        updatePagination();
      }
    },
    prevPage: function() {
      if (currentPage > 1) {
        currentPage--;
        renderSessionsTable();
        updatePagination();
      }
    }
  };
});