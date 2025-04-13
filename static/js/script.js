// Global variables
let currentYear;
let currentMonth;
let selectedDate = null;
let selectedTime = null;

document.addEventListener('DOMContentLoaded', function() {
    // Get current date
    const currentDate = new Date();
    currentMonth = currentDate.getMonth();
    currentYear = currentDate.getFullYear();
    
    // Function to update the calendar display
    function updateCalendar() {
        const calendarDays = document.getElementById('calendarDays');
        const currentMonthDisplay = document.getElementById('currentMonth');
        
        // Clear existing calendar days
        calendarDays.innerHTML = '';
        
        // Update month and year display
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'];
        currentMonthDisplay.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        
        // Get first day of the month
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        
        // Get number of days in the month
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        
        // Add empty cells for days before the 1st of the month
        for (let i = 0; i < firstDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day';
            calendarDays.appendChild(emptyDay);
        }
        
        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            
            // Check if the date is in the past
            const currentDate = new Date();
            const currentDay = new Date(currentYear, currentMonth, day);
            
            if (currentDay < currentDate) {
                dayElement.classList.add('disabled');
            }
            
            dayElement.textContent = day;
            
            // Add click event listener
            dayElement.addEventListener('click', function() {
                if (!this.classList.contains('disabled')) {
                    // Remove active class from all days
                    document.querySelectorAll('.calendar-day').forEach(el => {
                        el.classList.remove('active');
                    });
                    // Add active class to clicked day
                    this.classList.add('active');
                    
                    // Store selected date
                    selectedDate = new Date(currentYear, currentMonth, day);
                }
            });
            
            calendarDays.appendChild(dayElement);
        }
    }
    
    // Handle month navigation
    document.getElementById('prevMonth').addEventListener('click', function() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        updateCalendar();
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        updateCalendar();
    });
    
    // Initialize calendar
    updateCalendar();
    
    // Initialize timezone display
    displayAtlantaTimezone();
    
    // Update timezone every minute
    setInterval(displayAtlantaTimezone, 60000);
});

// Function to generate all time slots
function generateTimeSlots() {
    const slots = [];
    let hour = 8;
    let minute = 36;
    
    while (hour < 19 || (hour === 19 && minute === 0)) { // Until exactly 19:00
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour > 12 ? hour - 12 : hour;
        const timeStr = `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
        slots.push(timeStr);
        
        minute += 12;
        if (minute >= 60) {
            hour++;
            minute = 0;
        }
    }
    
    return slots;
}

// Function to handle time slot clicks and panel management
function setupTimeSlots() {
    const timeSlotsContainer = document.querySelector('.time-slots');
    const navButtons = document.querySelectorAll('.time-nav-btn');
    const modal = document.getElementById('confirmationModal');
    const confirmationText = document.getElementById('confirmationText');
    const cancelBtn = document.querySelector('.cancel-btn');
    const confirmBtn = document.querySelector('.modal-footer .confirm-btn');
    const bookNowBtn = document.querySelector('.book-button');
    let currentPanel = 0;
    let selectedTime = null;
    let selectedDate = null;
    
    // Generate all time slots
    const allTimeSlots = generateTimeSlots();
    
    // Split time slots into panels
    const panels = [
        allTimeSlots.slice(0, 18),  // Panel 1: 8:36 AM - 12:00 PM
        allTimeSlots.slice(18, 36), // Panel 2: 12:12 PM - 3:48 PM
        allTimeSlots.slice(36, 53)  // Panel 3: 4:00 PM - 7:00 PM (17 slots)
    ];
    
    // Function to update time slots display
    function updateTimeSlots() {
        timeSlotsContainer.innerHTML = '';
        
        panels[currentPanel].forEach(time => {
            const slot = document.createElement('div');
            slot.className = 'time-slot';
            slot.innerHTML = `<div class="time-text">${time}</div>`;
            
            // Add click event listener for the time slot
            slot.addEventListener('click', () => {
                // Remove active class from all slots
                document.querySelectorAll('.time-slot').forEach(el => {
                    el.classList.remove('active');
                });
                
                // Add active class to clicked slot
                slot.classList.add('active');
                
                // Store selected time
                selectedTime = time;
            });
            
            timeSlotsContainer.appendChild(slot);
        });
        
        // Update navigation buttons
        navButtons[0].disabled = currentPanel === 0;
        navButtons[1].disabled = currentPanel === panels.length - 1;
    }
    
    // Handle navigation
    navButtons[0].addEventListener('click', () => {
        if (currentPanel > 0) {
            currentPanel--;
            updateTimeSlots();
        }
    });
    
    navButtons[1].addEventListener('click', () => {
        if (currentPanel < panels.length - 1) {
            currentPanel++;
            updateTimeSlots();
        }
    });
    
    // Handle Book Now button click
    bookNowBtn.addEventListener('click', () => {
        const activeDay = document.querySelector('.calendar-day.active');
        const activeTimeSlot = document.querySelector('.time-slot.active');
        
        if (activeDay && activeTimeSlot) {
            selectedDate = new Date(
                currentYear,
                currentMonth,
                parseInt(activeDay.textContent)
            );
            
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                              'July', 'August', 'September', 'October', 'November', 'December'];
            
            const dayName = dayNames[selectedDate.getDay()];
            const monthName = monthNames[selectedDate.getMonth()];
            const day = selectedDate.getDate();
            const year = selectedDate.getFullYear();
            
            confirmationText.textContent = `You have selected: ${dayName}, ${monthName} ${day}, ${year} at ${selectedTime}`;
            modal.style.display = 'flex';
        }
    });
    
    // Handle modal buttons
    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        // Re-enable the confirm button when modal is closed
        confirmBtn.disabled = false;
        confirmBtn.style.opacity = '1';
        confirmBtn.style.cursor = 'pointer';
    });
    
    // Also handle clicking outside the modal to close it
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
            // Re-enable the confirm button when modal is closed
            confirmBtn.disabled = false;
            confirmBtn.style.opacity = '1';
            confirmBtn.style.cursor = 'pointer';
        }
    });
    
    confirmBtn.addEventListener('click', async () => {
        if (selectedDate && selectedTime) {
            // Disable the confirm button to prevent multiple clicks
            confirmBtn.disabled = true;
            confirmBtn.style.opacity = '0.5';
            confirmBtn.style.cursor = 'not-allowed';
            
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        date: `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`,
                        time: selectedTime
                    })
                });

                const result = await response.json();
                
                if (result.status === 'success') {
                    alert('Reservation submitted successfully!');
                    modal.style.display = 'none';
                    // Re-enable the button after successful submission
                    confirmBtn.disabled = false;
                    confirmBtn.style.opacity = '1';
                    confirmBtn.style.cursor = 'pointer';
                } else {
                    alert('Error submitting reservation: ' + result.message);
                    modal.style.display = 'none';  // Close the modal on error
                    // Re-enable the button if there was an error
                    confirmBtn.disabled = false;
                    confirmBtn.style.opacity = '1';
                    confirmBtn.style.cursor = 'pointer';
                }
            } catch (error) {
                alert('Error submitting reservation. Please try again.');
                modal.style.display = 'none';  // Close the modal on error
                console.error('Error:', error);
                // Re-enable the button if there was an error
                confirmBtn.disabled = false;
                confirmBtn.style.opacity = '1';
                confirmBtn.style.cursor = 'pointer';
            }
        } else {
            alert('Please select both a date and time before confirming.');
        }
    });
    
    // Initialize time slots
    updateTimeSlots();
}

// Call the setup function when the document is loaded
document.addEventListener('DOMContentLoaded', setupTimeSlots);

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
    document.getElementById('timezoneDisplay').textContent = displayString;
}