document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        const participantsList = details.participants.length > 0
          ? details.participants.map(p => `<li><span>${p}</span><button class="delete-participant" data-activity="${name}" data-email="${p}" title="Remove participant">✕</button></li>`).join('')
          : '<li class="no-participants">No participants yet</li>';

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Registered Participants:</strong>
            <ul class="participants-list">
              ${participantsList}
            </ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
      // Add event listeners for delete buttons
      document.querySelectorAll(\".delete-participant\").forEach(button => {
        button.addEventListener(\"click\", async (event) => {
          event.preventDefault();
          const activityName = event.target.dataset.activity;
          const email = event.target.dataset.email;

          if (confirm(`Are you sure you want to unregister ${email} from ${activityName}?`)) {
            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(email)}`,
                { method: \"DELETE\" }
              );

              if (response.ok) {
                // Refresh activities to reflect changes
                fetchActivities();
                messageDiv.textContent = `Successfully unregistered ${email}`;
                messageDiv.className = \"success\";
                messageDiv.classList.remove(\"hidden\");
                setTimeout(() => messageDiv.classList.add(\"hidden\"), 5000);
              } else {
                const result = await response.json();
                messageDiv.textContent = result.detail || \"Failed to unregister\";
                messageDiv.className = \"error\";
                messageDiv.classList.remove(\"hidden\");
              }
            } catch (error) {
              messageDiv.textContent = \"Failed to unregister participant\";
              messageDiv.className = \"error\";
              messageDiv.classList.remove(\"hidden\");
              console.error(\"Error unregistering:\", error);
            }
          }
        });
      });    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
