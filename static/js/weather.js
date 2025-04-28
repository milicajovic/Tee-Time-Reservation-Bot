// static/js/weather.js
document.addEventListener('DOMContentLoaded', () => {
    // 1) Grab everything
    const calendar     = document.getElementById('calendarDays');
    const chatButton   = document.getElementById('chatButton');
    const chatWidget   = document.getElementById('chatWidget');
    const chatClose    = document.getElementById('chatClose');
    const notifBadge   = document.getElementById('notificationBadge');
    const chatBody     = document.getElementById('chatBody');
    const notifSound   = document.getElementById('notificationSound');
    const chatButtonClose = document.getElementById('chatButtonClose');
    let chatButtonClosed = false;
    let chatButtonShown = false;
  
    // 2) Chat toggle
    chatButton.addEventListener('click', () => {
      chatWidget.classList.toggle('active');
      chatButton.classList.toggle('hidden', chatWidget.classList.contains('active'));
      notifBadge.classList.remove('active');
    });
    chatClose.addEventListener('click', () => {
      chatWidget.classList.remove('active');
      chatButton.classList.remove('hidden');
    });
  
    // Show/hide close-X on hover only if badge is not active and chat is closed
    chatButton.addEventListener('mouseenter', () => {
      if (!notifBadge.classList.contains('active') && !chatWidget.classList.contains('active')) {
        chatButtonClose.style.display = 'flex';
      }
    });
    chatButton.addEventListener('mouseleave', () => {
      chatButtonClose.style.display = 'none';
    });

    chatButtonClose.addEventListener('click', (e) => {
      e.stopPropagation();
      chatButtonClosed = true;
      chatButton.style.display = 'none';
    });
  
    // 3) Notification sound
    function playNotificationSound() {
      notifSound.currentTime = 0;
      notifSound.play().catch(() => {});
    }
  
    // 4) Icon mapping
    const ICON_MAP = {
        "Clear sky":                  "wi-day-sunny",
        "Mainly clear":               "wi-day-sunny-overcast",
        "Partly cloudy":              "wi-day-cloudy",
        "Overcast":                   "wi-cloudy",
        "Fog":                        "wi-fog",
        "Depositing rime fog":        "wi-fog",
        "Light drizzle":              "wi-sprinkle",
        "Moderate drizzle":           "wi-sprinkle",
        "Dense drizzle":              "wi-sprinkle",
        "Light freezing drizzle":     "wi-sleet",
        "Dense freezing drizzle":     "wi-sleet",
        "Light rain":                 "wi-showers",
        "Moderate rain":              "wi-rain",
        "Heavy rain":                 "wi-rain-wind",
        "Light freezing rain":        "wi-rain-mix",
        "Heavy freezing rain":        "wi-rain-mix",
        "Slight snow fall":           "wi-snow",
        "Moderate snow fall":         "wi-snow",
        "Heavy snow fall":            "wi-snow-wind",
        "Snow grains":                "wi-snowflake-cold",
        "Slight rain showers":        "wi-showers",
        "Moderate rain showers":      "wi-showers",
        "Violent rain showers":       "wi-storm-showers",
        "Slight snow showers":        "wi-snow",
        "Heavy snow showers":         "wi-snow-wind",
        "Thunderstorm":               "wi-thunderstorm",
        "Thunderstorm with slight hail":"wi-hail",
        "Thunderstorm with heavy hail":"wi-hail"
    };

    // Returns "Month day, year" for "YYYY-MM-DD"
    function formatFriendlyDate(dateStr) {
        const [y, m, d] = dateStr.split('-');
        const dt = new Date(y, m - 1, d);
        return dt.toLocaleDateString('en-US', {
        month: 'long', day: 'numeric', year: 'numeric'
        });
    }

    // 5) Render into chat
    function showWeatherInChat(data) {
      if (chatButtonClosed) return;
      chatBody.innerHTML = '';
      if (!chatWidget.classList.contains('active')) {
        notifBadge.classList.add('active');
      } else {
        notifBadge.classList.remove('active');
      }
  
      let html;
      if (data.error) {
        html = `<div class="chat-message active">
                  <div class="message-content"><p>${data.error}</p></div>                  
                </div>`;
      }
      else if (data.temp_mean !== undefined) {
        // Climatology
        const f = (data.temp_mean * 9/5 + 32).toFixed(1);
        html = `<div class="chat-message active">
                  <div class="message-content">
                    <div>Average on ${data.date}:</div>
                    <strong>${f}°F</strong>
                    <em>${data.note}</em>
                  </div>
                </div>`;
      }
      else {
        // Forecast
        const friendly = formatFriendlyDate(data.date);
        const fmin = (data.temp_min * 9/5 + 32).toFixed(1);
        const fmax = (data.temp_max * 9/5 + 32).toFixed(1);
        const icon = ICON_MAP[data.description] || 'fa-question';
        
        // First message with date
        html = `<div class="chat-message active">
                  <div class="message-content">
                    <div class="weather-date">${friendly}</div>
                  </div>
                </div>`;
                
        // Second message with weather details
        html += `<div class="chat-message active">
                  <div class="message-content">
                    <div class="weather-details">
                      <i class="wi ${ICON_MAP[data.description]} wi-5x" style="margin-right:8px;"></i>
                      <div>
                        <div>${fmin}–${fmax}°F</div>
                        <div>${data.description}</div>
                      </div>
                    </div>
                  </div>
                </div>`;
      }
  
      chatBody.insertAdjacentHTML('beforeend', html);
      playNotificationSound();
    }
  
    // 6) Calendar click → fetch + console.log + chat
    calendar.addEventListener('click', e => {
      const td = e.target;
      if (!td.classList.contains('calendar-day') ||
          td.classList.contains('disabled') ||
          !td.textContent.trim()) return;
  
      // Show chat button on first calendar click if not closed
      if (!chatButtonShown && !chatButtonClosed) {
        chatButton.style.display = '';
        chatButtonShown = true;
      }
  
      const day   = td.textContent.trim().padStart(2,'0');
      const mon   = String(currentMonth+1).padStart(2,'0');
      const dateStr = `${currentYear}-${mon}-${day}`;
  
      fetch(`/weather?date=${dateStr}`)
        .then(r => r.json())
        .then(data => {
          // optional console output
          if (!data.error && data.temp_min !== undefined) {
            const fmin = (data.temp_min*9/5+32).toFixed(1);
            const fmax = (data.temp_max*9/5+32).toFixed(1);
            console.log(`Weather on ${dateStr}: ${fmin}–${fmax}°F, ${data.description}`);
          }
          // always push to chat
          showWeatherInChat(data);
        })
        .catch(_ => showWeatherInChat({ error: 'Unable to fetch weather.' }));
    });
  });


  
  