// Function to display Atlanta timezone
function displayAtlantaTimezone() {
    const now = new Date();
  
    // Get the "long" time zone name
    const dtfLong = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York',
        timeZoneName: 'long',
    });
    const longParts = dtfLong.formatToParts(now);
    const longTZName = longParts.find(part => part.type === 'timeZoneName').value;
    
    // Get the "shortOffset" version
    const dtfShortOffset = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York',
        timeZoneName: 'shortOffset',
    });
    const shortOffsetParts = dtfShortOffset.formatToParts(now);
    const shortOffset = shortOffsetParts.find(part => part.type === 'timeZoneName').value;
  
    // Combine them into a display string
    const displayString = `Timezone: ${longTZName} (${shortOffset})`;
  
    // Show it in the page
    const timezoneDisplay = document.getElementById('timezoneDisplay');
    if (timezoneDisplay) {
        timezoneDisplay.textContent = displayString;
    }
}

// Initialize timezone display on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize timezone display
    displayAtlantaTimezone();
    
    // Update timezone every minute
    setInterval(displayAtlantaTimezone, 60000);
}); 