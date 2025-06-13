/**
 * statistics.js
 * Handles statistics and charts functionality
 */
function initializeCharts() {
  console.log("Initializing charts...");
  if (typeof Chart === 'undefined') {
    console.error("Chart.js library is not loaded! Make sure the CDN link is working.");
    const containers = [
      document.getElementById('focusTimelineChart'),
      document.getElementById('distributionChartContainer')
    ];
    
    containers.forEach(container => {
      if (container) {
        container.innerHTML = `
          <div class="text-center p-6 text-red-600">
            <i class="fas fa-exclamation-triangle text-4xl mb-2"></i>
            <p>Chart.js library failed to load.</p>
            <p class="text-sm">Please check browser console for errors.</p>
          </div>
        `;
      }
    });
    return false;
  }
  
  console.log("Chart.js is properly loaded.");
  return true;
}

const Statistics = (function() {
  // Private methods
  // Update the requestVisualizationData function to use a debounced request approach
  // This prevents excessive session history requests
  let sessionHistoryRequestTimeout = null;

  function requestVisualizationData() {
      if (AppState.isDetecting()) {
          // If we're actively detecting, request live data
          console.log("Requesting live visualization data...");
          AppState.getSocket().emit("get_visualization_data");
      } else {
          // If we're not detecting, try to use cached data from sessionStorage
          const lastData = getLastVisualizationData();
          if (lastData) {
              console.log("Using cached visualization data from sessionStorage");
              handleVisualizationData(lastData);
          } else {
              console.log("No cached visualization data available");
              // No need to make a server request in this case
              // Just show empty charts/placeholders
              if (initializeCharts()) {
                  updateFocusTimelineChart([]);
                  updateDistributionChart([]);
              }
              updateHistoricalSessions([]);
          }
      }
      
      // Only request session history if we don't already have a pending request
      // This prevents multiple requests during the 5-second interval
      if (!sessionHistoryRequestTimeout) {
          sessionHistoryRequestTimeout = setTimeout(() => {
              console.log("Requesting session history data...");
              AppState.getSocket().emit('get_session_history');
              sessionHistoryRequestTimeout = null;
          }, 300);
      }
  }

  function clearVisualizationData() {
    // Clear from sessionStorage
    sessionStorage.removeItem('lastVisualizationData');
    
    // Clear chart instances
    const charts = AppState.getCharts();
    if (charts.focusChart) {
      charts.focusChart.destroy();
      AppState.setFocusChart(null);
    }
    if (charts.distributionChart) {
      charts.distributionChart.destroy();
      AppState.setDistributionChart(null);
    }
    
    console.log("Visualization data cleared");
  }
  
  function updateFocusTimelineChart(timelineData) {
    // Check if Chart object exists (Chart.js loaded)
    if (typeof Chart === 'undefined') return;
    
    const chartContainer = document.getElementById("focusTimelineChart");
    if (!chartContainer) return;

    if (!timelineData || timelineData.length === 0) {
      // Display placeholder if no data
      chartContainer.innerHTML = `
        <div class="flex justify-center items-center h-64">
          <div class="text-center p-6 text-gray-400">
            <i class="fas fa-chart-line text-4xl mb-2"></i>
            <p>Focus tracking visualization will appear here</p>
            <p class="text-sm">Start a session to collect data</p>
          </div>
        </div>
      `;
      return;
    }

    // Prepare the chart canvas if it doesn't exist
    if (!document.getElementById("focusTimelineCanvas")) {
      chartContainer.innerHTML = '<canvas id="focusTimelineCanvas"></canvas>';
    }

    const ctx = document.getElementById("focusTimelineCanvas").getContext("2d");
    const colors = getChartColors();

    // Prepare data for the chart
    const labels = timelineData.map((item) => item.time);
    const drowsyData = timelineData.map((item) => item.drowsy);
    const yawnData = timelineData.map((item) => item.yawn);
    const distractionData = timelineData.map((item) => item.distraction);

    // Create or update the chart
    const charts = AppState.getCharts();
    if (charts.focusChart) {
      // Update existing chart
      charts.focusChart.data.labels = labels;
      charts.focusChart.data.datasets[0].data = drowsyData;
      charts.focusChart.data.datasets[1].data = yawnData;
      charts.focusChart.data.datasets[2].data = distractionData;
      charts.focusChart.update();
    } else {
      // Create new chart
      const newChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Drowsy Events",
              data: drowsyData,
              backgroundColor: colors.drowsy,
              borderColor: colors.drowsy,
              borderWidth: 1,
            },
            {
              label: "Yawn Events",
              data: yawnData,
              backgroundColor: colors.yawn,
              borderColor: colors.yawn,
              borderWidth: 1,
            },
            {
              label: "Distraction Events",
              data: distractionData,
              backgroundColor: colors.distraction,
              borderColor: colors.distraction,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              stacked: true,
              title: {
                display: true,
                text: "Time",
              },
            },
            y: {
              stacked: true,
              beginAtZero: true,
              title: {
                display: true,
                text: "Number of Events",
              },
              ticks: {
                stepSize: 1,
              },
            },
          },
          plugins: {
            title: {
              display: true,
              text: "Focus Events Timeline",
            },
            tooltip: {
              mode: "index",
              intersect: false,
            },
            legend: {
              position: "top",
            },
          },
        },
      });
      
      // Store chart reference
      AppState.setFocusChart(newChart);
    }
  }
  
  function updateDistributionChart(distributionData) {
    // Check if Chart object exists (Chart.js loaded)
    if (typeof Chart === 'undefined') return;
    
    const chartContainer = document.getElementById("distributionChartContainer");
    if (!chartContainer) return;

    if (!distributionData || distributionData.length === 0) {
      // Display placeholder if no data
      chartContainer.innerHTML = `
        <div class="flex justify-center items-center h-64">
          <div class="text-center p-6 text-gray-400">
            <i class="fas fa-chart-pie text-4xl mb-2"></i>
            <p>Event distribution chart will appear here</p>
            <p class="text-sm">Start a session to collect data</p>
          </div>
        </div>
      `;
      return;
    }

    // Prepare the chart canvas if it doesn't exist
    if (!document.getElementById("distributionChartCanvas")) {
      chartContainer.innerHTML = '<canvas id="distributionChartCanvas"></canvas>';
    }

    const ctx = document.getElementById("distributionChartCanvas").getContext("2d");
    const colors = getChartColors();

    // Prepare data for the chart
    const labels = distributionData.map((item) => item.name);
    const data = distributionData.map((item) => item.value);
    const backgroundColors = [
      colors.drowsy,
      colors.yawn,
      colors.distraction,
    ];

    // Create or update the chart
    const charts = AppState.getCharts();
    if (charts.distributionChart) {
      // Update existing chart
      charts.distributionChart.data.labels = labels;
      charts.distributionChart.data.datasets[0].data = data;
      charts.distributionChart.update();
    } else {
      // Create new chart
      const newChart = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: labels,
          datasets: [
            {
              data: data,
              backgroundColor: backgroundColors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: "Event Distribution",
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const label = context.label || "";
                  const value = context.formattedValue || "";
                  const dataset = context.dataset.data;
                  const total = dataset.reduce(
                    (acc, current) => acc + current,
                    0
                  );
                  const percentage = Math.round(
                    (context.raw / total) * 100
                  );
                  return `${label}: ${value} (${percentage}%)`;
                },
              },
            },
            legend: {
              position: "top",
            },
          },
        },
      });
      
      // Store chart reference
      AppState.setDistributionChart(newChart);
    }
  }

  let currentPage = 1;
  const sessionsPerPage = 10;
  let allSessions = [];
  
    /**
   * Updates historical sessions while preserving pagination state
   * @param {Array} sessions - New session data from server
   * @param {boolean} preservePage - Whether to preserve current page (default: true)
   */
  function updateHistoricalSessions(sessions, preservePage = true) {
    const tableBody = document.querySelector("#sessionsTable tbody");
    if (!tableBody) return;

    // Store all sessions for pagination
    if (sessions && sessions.length > 0) {
        allSessions = [...sessions];
    }

    if (!allSessions || allSessions.length === 0) {
        tableBody.innerHTML = `
            <tr class="text-center">
                <td colspan="5" class="px-6 py-8 text-gray-400">
                    No previous sessions recorded
                </td>
            </tr>
        `;
        
        // Hide pagination if no data
        const paginationContainer = document.getElementById('sessionsPagination');
        if (paginationContainer) {
            paginationContainer.classList.add('hidden');
        }
        return;
    }

    // Calculate pagination values
    const totalPages = Math.ceil(allSessions.length / sessionsPerPage);
    
    // Only reset the page if explicitly requested or if current page is invalid
    if (!preservePage) {
        currentPage = 1;
    } else if (currentPage > totalPages) {
        currentPage = totalPages;
    } else if (currentPage < 1) {
        currentPage = 1;
    }

    // Get the sessions for the current page
    const startIndex = (currentPage - 1) * sessionsPerPage;
    const endIndex = Math.min(startIndex + sessionsPerPage, allSessions.length);
    const currentPageSessions = allSessions.slice(startIndex, endIndex);

    // Create table rows
    let html = "";

    currentPageSessions.forEach((session) => {
        html += `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">${session.date || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap">${session.duration || 0} min</td>
                <td class="px-6 py-4 whitespace-nowrap">${session.drowsy || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap">${session.yawn || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap">${session.distraction || 0}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
    
    // Update pagination controls
    updatePaginationControls(totalPages);
    
    console.log(`Showing page ${currentPage} of ${totalPages} (preserving pagination: ${preservePage})`);
  }
  
  function updatePaginationControls(totalPages) {
    const paginationContainer = document.getElementById('sessionsPagination');
    if (!paginationContainer) return;
    
    // Show pagination if we have more than one page
    if (totalPages > 1) {
      paginationContainer.classList.remove('hidden');
      
      // Create pagination HTML
      let paginationHTML = `
        <div class="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
          <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-gray-700">
                Showing <span class="font-medium">${(currentPage - 1) * sessionsPerPage + 1}</span> to 
                <span class="font-medium">${Math.min(currentPage * sessionsPerPage, allSessions.length)}</span> of 
                <span class="font-medium">${allSessions.length}</span> results
              </p>
            </div>
            <div>
              <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <!-- Previous Page Button -->
                <button 
                  class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${currentPage === 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}" 
                  ${currentPage === 1 ? 'disabled' : ''}
                  onclick="Statistics.previousPage()">
                  <span class="sr-only">Previous</span>
                  <i class="fas fa-chevron-left"></i>
                </button>
                
                <!-- Page Numbers (simplified to show current page of total) -->
                <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                  Page ${currentPage} of ${totalPages}
                </span>
                
                <!-- Next Page Button -->
                <button 
                  class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${currentPage === totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}" 
                  ${currentPage === totalPages ? 'disabled' : ''}
                  onclick="Statistics.nextPage()">
                  <span class="sr-only">Next</span>
                  <i class="fas fa-chevron-right"></i>
                </button>
              </nav>
            </div>
          </div>
        </div>
      `;
      
      paginationContainer.innerHTML = paginationHTML;
    } else {
      // Hide pagination if only one page
      paginationContainer.classList.add('hidden');
    }
  }
  
  function nextPage() {
    if (currentPage < Math.ceil(allSessions.length / sessionsPerPage)) {
      currentPage++;
      updateHistoricalSessions();
    }
  }
  
  function previousPage() {
    if (currentPage > 1) {
      currentPage--;
      updateHistoricalSessions();
    }
  }

  function resetPage() {
    currentPage = 1;
  }
  
  function updatePointTrendChart(trendData) {
    const chartContainer = document.getElementById('pointTrendChart');
    if (!chartContainer) return;
    
    // Prepare the chart canvas if it doesn't exist
    if (!document.getElementById('pointTrendCanvas')) {
      chartContainer.innerHTML = '<canvas id="pointTrendCanvas"></canvas>';
    }
    
    const ctx = document.getElementById('pointTrendCanvas').getContext('2d');
    
    // Prepare data for chart
    const labels = trendData.map(day => {
      // Format date as "Mon 12" or similar
      const date = new Date(day.date);
      return date.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });
    });
    
    const points = trendData.map(day => day.points);
    
    // Create or update chart
    const charts = AppState.getCharts();
    if (charts.pointTrendChart) {
      charts.pointTrendChart.data.labels = labels;
      charts.pointTrendChart.data.datasets[0].data = points;
      charts.pointTrendChart.update();
    } else {
      const newChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Points Earned',
            data: points,
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Points'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date'
              }
            }
          },
          plugins: {
            tooltip: {
              mode: 'index',
              intersect: false
            },
            legend: {
              display: false
            }
          }
        }
      });
      
      // Store chart reference
      AppState.setPointTrendChart(newChart);
    }
  }
  
  function getChartColors() {
    return {
      drowsy: "rgba(220, 53, 69, 0.8)",  // red
      yawn: "rgba(255, 193, 7, 0.8)",    // yellow
      distraction: "rgba(253, 126, 20, 0.8)", // orange
      focus: "rgba(13, 110, 253, 0.8)"   // blue
    };
  }
  
  function handleStatisticsUpdate(stats) {
    // Update statistics in statistics tab
    const sessionDuration = document.getElementById("sessionDuration");
    const drowsyEvents = document.getElementById("drowsyEvents");
    const yawnEvents = document.getElementById("yawnEvents");
    const distractionEvents = document.getElementById("distractionEvents");
    
    if (sessionDuration) sessionDuration.textContent = `${stats.session_duration} min`;
    if (drowsyEvents) drowsyEvents.textContent = stats.total_drowsy_events;
    if (yawnEvents) yawnEvents.textContent = stats.total_yawn_events;
    if (distractionEvents) distractionEvents.textContent = stats.total_distraction_events;
  }
  
  function handleVisualizationData(data) {
    console.log("Handling visualization data:", data);
    
    if (!data) {
      console.error("No visualization data received");
      return;
    }
    
    // Store the data in sessionStorage for persistence during the same login session
    saveVisualizationData(data);
    
    // Check if we have the expected data structure
    if (!data.timeline) console.warn("Missing timeline data");
    if (!data.distribution) console.warn("Missing distribution data");
    if (!data.historical) console.warn("Missing historical data");
    
    // If we have session_info, update the summary stats
    if (data.session_info) {
      updateSessionSummary(data.session_info);
    } 
    // If no direct session_info, try to extract it from timeline or distribution data
    else if (data.timeline && data.timeline.length > 0 || data.distribution && data.distribution.length > 0) {
      // Construct session info from timeline/distribution data
      const sessionInfo = {
        duration: 0,
        drowsy_events: 0,
        yawn_events: 0,
        distraction_events: 0
      };
      
      // Extract duration from historical data if available
      if (data.historical && data.historical.length > 0) {
        sessionInfo.duration = data.historical[0].duration || 0;
      }
      
      // Extract event counts from distribution data
      if (data.distribution && data.distribution.length > 0) {
        data.distribution.forEach(item => {
          if (item.name.includes('Drowsy')) {
            sessionInfo.drowsy_events = item.value || 0;
          } else if (item.name.includes('Yawn')) {
            sessionInfo.yawn_events = item.value || 0;
          } else if (item.name.includes('Distraction')) {
            sessionInfo.distraction_events = item.value || 0;
          }
        });
      }
      
      // Extract event counts from timeline data if not available from distribution
      if ((!sessionInfo.drowsy_events && !sessionInfo.yawn_events && !sessionInfo.distraction_events) && 
          data.timeline && data.timeline.length > 0) {
        sessionInfo.drowsy_events = data.timeline.reduce((sum, item) => sum + (item.drowsy || 0), 0);
        sessionInfo.yawn_events = data.timeline.reduce((sum, item) => sum + (item.yawn || 0), 0);
        sessionInfo.distraction_events = data.timeline.reduce((sum, item) => sum + (item.distraction || 0), 0);
      }
      
      // Update with extracted info
      if (sessionInfo.drowsy_events > 0 || sessionInfo.yawn_events > 0 || 
          sessionInfo.distraction_events > 0 || sessionInfo.duration > 0) {
        console.log("Extracted session info from visualization data:", sessionInfo);
        updateSessionSummary(sessionInfo);
      }
    }
    
    // Check if Chart.js is available before trying to create charts
    if (initializeCharts()) {
      updateFocusTimelineChart(data.timeline);
      updateDistributionChart(data.distribution);
    }
    
    // Update historical sessions
    if (data.historical) {
      updateHistoricalSessions(data.historical);
    }
  }

  function updateSessionSummary(sessionInfo) {
    // Update statistics in statistics tab
    if (!sessionInfo) {
      console.warn("No session info available for updating summary");
      return;
    }
    
    const sessionDuration = document.getElementById("sessionDuration");
    const drowsyEvents = document.getElementById("drowsyEvents");
    const yawnEvents = document.getElementById("yawnEvents");
    const distractionEvents = document.getElementById("distractionEvents");
    
    if (sessionDuration) sessionDuration.textContent = `${sessionInfo.duration || 0} min`;
    if (drowsyEvents) drowsyEvents.textContent = sessionInfo.drowsy_events || 0;
    if (yawnEvents) yawnEvents.textContent = sessionInfo.yawn_events || 0;
    if (distractionEvents) distractionEvents.textContent = sessionInfo.distraction_events || 0;
    
    console.log("Session summary updated:", sessionInfo);
  }
  
  function updateAnalyticsDisplay(data) {
    if (!data || data.error) {
      console.error("Error updating analytics:", data?.error || "No data received");
      return;
    }
    
    console.log("Received analytics data:", data);
    
    // Update engagement metrics if elements exist
    const totalSessions = document.getElementById('totalSessions');
    if (totalSessions) totalSessions.textContent = data.engagement?.total_sessions || data.sessions || 0;
    
    const totalFocusTime = document.getElementById('totalFocusTime');
    if (totalFocusTime) {
      const minutes = data.engagement?.total_focus_minutes || data.focus_minutes || 0;
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      totalFocusTime.textContent = hours > 0 ? 
        `${hours}h ${remainingMinutes}m` : `${minutes}m`;
    }
    
    const avgDailyFocus = document.getElementById('avgDailyFocus');
    if (avgDailyFocus) {
      const avg = data.engagement?.avg_daily_focus || 0;
      avgDailyFocus.textContent = `${avg} min`;
    }
    
    const totalPomodoros = document.getElementById('totalPomodoros');
    if (totalPomodoros) {
      totalPomodoros.textContent = data.engagement?.total_pomodoros || data.pomodoro_streak || 0;
    }
    
    // Update milestone progress bars
    updateMilestoneProgressBars(data);
    
    // Update point trend chart if Chart.js is available
    if (typeof Chart !== 'undefined' && data.point_trend && data.point_trend.length > 0) {
      updatePointTrendChart(data.point_trend);
    } else if (typeof Chart !== 'undefined') {
      // If no point trend data, create sample data
      const sampleTrendData = createSampleTrendData(data.daily_streak || 1);
      updatePointTrendChart(sampleTrendData);
    }
  }

  function createSampleTrendData(days) {
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < Math.min(days, 7); i++) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      data.unshift({
        date: date.toISOString().split('T')[0],
        points: Math.floor(Math.random() * 50) + 20 // Random points between 20-70
      });
    }
    
    return data;
  }

  function updateMilestoneProgressBars(data) {
    // Focus time milestone (1 hour)
    const focusMinutes = data.focus_minutes || data.engagement?.total_focus_minutes || 0;
    const focusHourProgress = Math.min(100, (focusMinutes / 60) * 100);
    updateMilestoneBar('milestone1Bar', 'milestone1Progress', focusHourProgress);
    
    // Sessions milestone (5 sessions)
    const sessions = data.sessions || data.engagement?.total_sessions || 0;
    const sessionsProgress = Math.min(100, (sessions / 5) * 100);
    updateMilestoneBar('milestone2Bar', 'milestone2Progress', sessionsProgress);
    
    // Pomodoro milestone (10 sessions)
    const pomodoros = data.pomodoro_streak || data.engagement?.total_pomodoros || 0;
    const pomodoroProgress = Math.min(100, (pomodoros / 10) * 100);
    updateMilestoneBar('milestone3Bar', 'milestone3Progress', pomodoroProgress);
  }

  function updateMilestoneBar(barId, textId, progress) {
    const bar = document.getElementById(barId);
    const text = document.getElementById(textId);
    
    if (bar) bar.style.width = `${progress}%`;
    if (text) text.textContent = `${Math.round(progress)}%`;
  }

  function getLastVisualizationData() {
    try {
      const savedData = sessionStorage.getItem('lastVisualizationData');
      return savedData ? JSON.parse(savedData) : null;
    } catch (e) {
      console.error("Error retrieving visualization data from session storage:", e);
      return null;
    }
  }

  function saveVisualizationData(data) {
    try {
      sessionStorage.setItem('lastVisualizationData', JSON.stringify(data));
    } catch (e) {
      console.error("Error saving visualization data to session storage:", e);
    }
  }

  function initializeExportButton() {
    const exportButton = document.querySelector('button.text-blue-600.hover\\:text-blue-800.text-sm.font-medium');
    
    if (exportButton) {
      exportButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Show loading state
        const originalText = exportButton.innerHTML;
        exportButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Exporting...';
        exportButton.disabled = true;
        
        // Create a download in a new tab/window
        window.open('/api/export_session_history', '_blank');
        
        // Reset button after a short delay
        setTimeout(() => {
          exportButton.innerHTML = originalText;
          exportButton.disabled = false;
          
          // Show success notification
          if (typeof Notifications !== 'undefined' && Notifications.showNotification) {
            Notifications.showNotification('Session history exported successfully', 'success');
          }
        }, 1500);
      });
      
      console.log('Export button handler initialized');
    } else {
      console.warn('Export button not found');
    }
  }

  // Public methods
  return {
    requestVisualizationData: requestVisualizationData,
    handleStatisticsUpdate: handleStatisticsUpdate,
    handleVisualizationData: handleVisualizationData,
    updateAnalyticsDisplay: updateAnalyticsDisplay,
    clearVisualizationData: clearVisualizationData,
    updateHistoricalSessions: updateHistoricalSessions, // Expose this for direct use by socket handlers
    initializeExportButton: initializeExportButton,
    nextPage: nextPage,
    previousPage: previousPage,
    resetPage: resetPage
  };
})();

// Export the Statistics namespace
window.Statistics = Statistics;

// Setup session history socket handler - moved outside the module to prevent multiple registrations
AppState.getSocket().on('session_history_data', function(data) {
  console.log("Received session history data:", data);
  
  if (data && Array.isArray(data.sessions)) {
    // Update the sessions table with the received data
    Statistics.updateHistoricalSessions(data.sessions);
  } else {
    console.warn("Invalid session history data received:", data);
    Statistics.updateHistoricalSessions([]);
  }
});

// Initialize on page load
document.addEventListener("DOMContentLoaded", function() {
  // Initialize charts
  initializeCharts();
  
  // Initialize export button
  Statistics.initializeExportButton();
  
  console.log('Statistics module initialized');
});