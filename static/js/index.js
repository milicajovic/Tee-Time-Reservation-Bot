// Global variables
let currentView = 'dateTime';
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let selectedDate = null;
let selectedTime = null;
let selectedTimeRange = '0';  // Default to '0' (Exact)
let selectedHour = 8;
let selectedMinute = 0;
let selectedPeriod = 'AM';
let currentPanel = 0;
let panels = [];

document.addEventListener('DOMContentLoaded', function() {
    // Get current date
    const currentDate = new Date();
    currentMonth = currentDate.getMonth();
    currentYear = currentDate.getFullYear();
    
    // View navigation elements
    const calendarContainer = document.querySelector('.calendar-container');
    const emptyContainer = document.querySelector('.empty-container');
    const prevViewBtn = document.getElementById('prevView');
    const nextViewBtn = document.getElementById('nextView');
    
    // Handle view navigation
    nextViewBtn.addEventListener('click', function() {
        calendarContainer.style.display = 'none';
        emptyContainer.style.display = 'block';
        prevViewBtn.style.display = 'flex';
        nextViewBtn.style.display = 'none';
        // Change the title text
        document.querySelector('.select-date-and-time-title').textContent = 'Reservations';
        // Hide the Book Now button
        document.querySelector('.book-button').style.display = 'none';
        // Fetch and display reservations
        fetchAndDisplayReservations();
    });
    
    prevViewBtn.addEventListener('click', function() {
        calendarContainer.style.display = 'flex';
        emptyContainer.style.display = 'none';
        prevViewBtn.style.display = 'none';
        nextViewBtn.style.display = 'flex';
        // Change the title text back
        document.querySelector('.select-date-and-time-title').textContent = 'Select Date and Time';
        // Show the Book Now button
        document.querySelector('.book-button').style.display = 'block';
    });
    
    // Initially hide the back button
    prevViewBtn.style.display = 'none';
    
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
            
            // Check if the date is in the past (excluding current day)
            const currentDate = new Date();
            const currentDay = new Date(currentYear, currentMonth, day);
            
            // Only disable if the date is before today (not including today)
            if (currentDay < new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate())) {
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
                    
                    // Make sure time range boxes are generated
                    if (!document.querySelector('.time-range-box')) {
                        generateTimeRangeBoxes();
                    }
                    
                    // Update the time for Monday special case
                    if (selectedDate.getDay() === 1) { // Monday
                        // Set initial time to 8:36 AM for Mondays
                        selectedHour = 8;
                        selectedMinute = 36;
                        selectedPeriod = 'AM';
                        
                        // Update the time picker UI
                        const hourValue = document.getElementById('hour-value');
                        const minuteValue = document.getElementById('minute-value');
                        const periodValue = document.getElementById('period-value');
                        
                        if (hourValue && minuteValue && periodValue) {
                            hourValue.textContent = selectedHour;
                            minuteValue.textContent = selectedMinute.toString().padStart(2, '0');
                            periodValue.textContent = selectedPeriod;
                            
                            // Update the formatted time
                            selectedTime = `${selectedHour}:${selectedMinute.toString().padStart(2, '0')} ${selectedPeriod}`;
                        }
                    }
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

    // Handle delete reservation buttons
    document.querySelectorAll('.delete-reservation-btn').forEach(button => {
        button.addEventListener('click', function() {
            const reservationRow = this.closest('.reservation-row');
            const reservationDate = reservationRow.querySelector('.reservation-date').textContent;
            
            if (confirm(`Are you sure you want to delete the reservation for ${reservationDate}?`)) {
                reservationRow.remove();
            }
        });
    });

    // Course dropdown functionality
    const courseDropdownContainer = document.querySelector('.course-dropdown-container');
    const courseDropdownButton = document.querySelector('.course-dropdown-button');
    const courseDropdownOptions = document.querySelector('.course-dropdown-options');
    const selectedValue = document.querySelector('.selected-value');

    // Toggle dropdown
    courseDropdownButton.addEventListener('click', function(e) {
        e.stopPropagation();
        courseDropdownContainer.classList.toggle('active');
    });

    // Handle option selection
    courseDropdownOptions.addEventListener('click', function(e) {
        const option = e.target.closest('.course-dropdown-option');
        if (!option) return;

        // Update selected value
        selectedValue.textContent = option.textContent;
        
        // Update selected state
        courseDropdownOptions.querySelectorAll('.course-dropdown-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        option.classList.add('selected');

        // Close dropdown
        courseDropdownContainer.classList.remove('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!courseDropdownContainer.contains(e.target)) {
            courseDropdownContainer.classList.remove('active');
        }
    });
});

// Function to handle time selection with the new time picker
function setupTimePicker() {
    const hourValue = document.getElementById('hour-value');
    const minuteValue = document.getElementById('minute-value');
    const periodValue = document.getElementById('period-value');
    
    const hourPrev = document.getElementById('hour-prev');
    const hourNext = document.getElementById('hour-next');
    const minutePrev = document.getElementById('minute-prev');
    const minuteNext = document.getElementById('minute-next');
    const periodPrev = document.getElementById('period-prev');
    const periodNext = document.getElementById('period-next');
    
    const modal = document.getElementById('confirmationModal');
    const confirmationText = document.getElementById('confirmationText');
    const cancelBtn = document.querySelector('.cancel-btn');
    const confirmBtn = document.querySelector('.modal-footer .confirm-btn');
    const bookNowBtn = document.querySelector('.book-button');
    const timeRangeContainer = document.querySelector('.time-range-container');
    const timeRangePrev = document.querySelector('.time-range-prev');
    const timeRangeNext = document.querySelector('.time-range-next');
    
    // Available hours: 1-12
    const hours = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    
    // Available minutes: 00, 12, 24, 36, 48
    const minutes = [0, 12, 24, 36, 48];
    
    // Available periods: AM, PM
    const periods = ['AM', 'PM'];
    
    // Set initial values
    hourValue.textContent = selectedHour;
    minuteValue.textContent = selectedMinute.toString().padStart(2, '0');
    periodValue.textContent = selectedPeriod;
    
    // Update the formatted time
    function updateSelectedTime() {
        selectedTime = `${selectedHour}:${selectedMinute.toString().padStart(2, '0')} ${selectedPeriod}`;
        console.log(`Selected time: ${selectedTime}`);
    }
    
    // Initialize the time on page load
    updateSelectedTime();
    
    // Handle hour navigation
    hourPrev.addEventListener('click', () => {
        const currentIndex = hours.indexOf(selectedHour);
        const newIndex = (currentIndex - 1 + hours.length) % hours.length;
        selectedHour = hours[newIndex];
        hourValue.textContent = selectedHour;
        updateSelectedTime();
    });
    
    hourNext.addEventListener('click', () => {
        const currentIndex = hours.indexOf(selectedHour);
        const newIndex = (currentIndex + 1) % hours.length;
        selectedHour = hours[newIndex];
        hourValue.textContent = selectedHour;
        updateSelectedTime();
    });
    
    // Handle minute navigation
    minutePrev.addEventListener('click', () => {
        const currentIndex = minutes.indexOf(selectedMinute);
        const newIndex = (currentIndex - 1 + minutes.length) % minutes.length;
        selectedMinute = minutes[newIndex];
        minuteValue.textContent = selectedMinute.toString().padStart(2, '0');
        updateSelectedTime();
    });
    
    minuteNext.addEventListener('click', () => {
        const currentIndex = minutes.indexOf(selectedMinute);
        const newIndex = (currentIndex + 1) % minutes.length;
        selectedMinute = minutes[newIndex];
        minuteValue.textContent = selectedMinute.toString().padStart(2, '0');
        updateSelectedTime();
    });
    
    // Handle period navigation
    periodPrev.addEventListener('click', () => {
        selectedPeriod = selectedPeriod === 'AM' ? 'PM' : 'AM';
        periodValue.textContent = selectedPeriod;
        updateSelectedTime();
    });
    
    periodNext.addEventListener('click', () => {
        selectedPeriod = selectedPeriod === 'AM' ? 'PM' : 'AM';
        periodValue.textContent = selectedPeriod;
        updateSelectedTime();
    });
    
    // Generate time range boxes
    window.generateTimeRangeBoxes = function() {
        timeRangeContainer.innerHTML = '';
        
        const ranges = [
            { value: '0', text: 'Exact time' },
            { value: '12', text: '+12 min' },
            { value: '24', text: '+24 min' },
            { value: '36', text: '+36 min' },
            { value: '48', text: '+48 min' },
            { value: '60', text: '+1 hr' },
            { value: '120', text: '+2 hr' },
            { value: '180', text: '+3 hr' },
            { value: '240', text: '+4 hr' },
            { value: '300', text: '+5 hr' }
        ];
        
        // Create time range boxes without wrapper
        ranges.forEach(range => {
            const box = document.createElement('div');
            box.className = 'time-range-box';
            if (range.value === selectedTimeRange) {
                box.classList.add('selected');
            }
            box.dataset.value = range.value;
            box.textContent = range.text;
            
            box.addEventListener('click', () => {
                // Remove selected class from all boxes
                document.querySelectorAll('.time-range-box').forEach(b => {
                    b.classList.remove('selected');
                });
                
                // Add selected class to clicked box
                box.classList.add('selected');
                
                // Store the selected range
                selectedTimeRange = range.value;
                console.log(`Selected time range: ${range.text} (${range.value})`);
            });
            
            timeRangeContainer.appendChild(box);
        });
        
        // No need for slider navigation in this UI design
    };
    
    // Handle Book Now button click
    bookNowBtn.addEventListener('click', () => {
        const activeDay = document.querySelector('.calendar-day.active');
        const selectedRangeBox = document.querySelector('.time-range-box.selected');
        
        if (activeDay) {
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
            
            const rangeText = selectedRangeBox ? ` (${selectedRangeBox.textContent})` : '';
            confirmationText.textContent = `You have selected: ${dayName}, ${monthName} ${day}, ${year} at ${selectedTime}${rangeText}`;
            modal.style.display = 'flex';
        } else {
            alert('Please select a date before confirming.');
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
        if (selectedDate) {
            // Add loading state to the button
            confirmBtn.classList.add('loading');
            confirmBtn.disabled = true;
            
            try {
                // Get the selected course value
                const selectedCourse = document.querySelector('.course-dropdown-option.selected').dataset.value;
                
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        date: `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`,
                        time: selectedTime,
                        time_slot_range: selectedTimeRange,
                        course: selectedCourse
                    })
                });

                const result = await response.json();
                
                // Remove loading state
                confirmBtn.classList.remove('loading');
                confirmBtn.disabled = false;
                
                if (result.status === 'success') {
                    alert('Reservation submitted successfully!');
                    modal.style.display = 'none';
                    
                    // Clear the selected values
                    selectedDate = null;
                    
                    // Reset time range selection
                    selectedTimeRange = '0';
                    document.querySelectorAll('.time-range-box').forEach(box => {
                        box.classList.remove('selected');
                        if (box.dataset.value === '0') {
                            box.classList.add('selected');
                        }
                    });
                    
                    // Remove active class from calendar day
                    const activeDay = document.querySelector('.calendar-day.active');
                    if (activeDay) {
                        activeDay.classList.remove('active');
                    }
                } else {
                    alert('Error submitting reservation: ' + result.message);
                    modal.style.display = 'none';
                }
            } catch (error) {
                // Remove loading state on error
                confirmBtn.classList.remove('loading');
                confirmBtn.disabled = false;
                
                alert('Error submitting reservation. Please try again.');
                modal.style.display = 'none';
                console.error('Error:', error);
            }
        } else {
            alert('Please select a date before confirming.');
        }
    });
    
    // Initialize time range boxes
    generateTimeRangeBoxes();
}

// Call the setup function when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize time picker
    setupTimePicker();
});

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

// Function to format date from YYYY-MM-DD to Month DDth, YYYY
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    const day = date.getDate();
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();
    
    // Add the appropriate suffix to the day
    let suffix = 'th';
    if (day % 10 === 1 && day !== 11) suffix = 'st';
    else if (day % 10 === 2 && day !== 12) suffix = 'nd';
    else if (day % 10 === 3 && day !== 13) suffix = 'rd';
    
    return `${month} ${day}${suffix}, ${year}`;
}

// Function to format time from HH:MM AM/PM to HH:MM am/pm
function formatTime(timeStr) {
    return timeStr.toLowerCase();
}

// Function to create a reservation row
function createReservationRow(reservation) {
    const row = document.createElement('div');
    row.className = 'reservation-row';
    
    const formattedDate = formatDate(reservation.date);
    const formattedTime = formatTime(reservation.time);
    
    // Determine which external link icon to use and if it should be clickable
    const shouldShowEnabledLink = reservation.status === 'failed' || 
                                 reservation.status === 'executed' || 
                                 (reservation.status === 'pending' && reservation.retry_count > 0);
    
    const externalLinkIcon = shouldShowEnabledLink ? 
        'external-link-enabled.png' : 
        'external-link-disabled.png';
    
    row.innerHTML = `
        <div class="reservation-date">${formattedDate} at ${formattedTime}</div>
        <div class="reservation-status ${reservation.status}">${reservation.status}</div>
        <div class="reservation-action">
            <img src="/static/images/${externalLinkIcon}" alt="External Link" class="external-link-icon" style="cursor: pointer; margin-right: 8px; width: 20px; height: 20px; vertical-align: middle;">
            <button class="delete-reservation-btn" ${reservation.status !== 'pending' ? 'disabled' : ''}>
                Cancel
            </button>
        </div>
    `;
    
    // Add click event listener for the cancel button
    const cancelBtn = row.querySelector('.delete-reservation-btn');
    if (reservation.status === 'pending') {
        cancelBtn.addEventListener('click', function() {
            if (confirm(`Are you sure you want to cancel the reservation for ${formattedDate} at ${formattedTime}?`)) {
                cancelReservation(reservation.date, reservation.time, row);
            }
        });
    }
    
    // Add click event listener for the external link icon
    const externalLinkImg = row.querySelector('.external-link-icon');
    if (shouldShowEnabledLink && reservation.screenshot_folder_url) {
        externalLinkImg.addEventListener('click', function() {
            // Extract date and time from the reservation
            const date = reservation.date;
            const time = reservation.time;
            // Navigate to gallery.html with parameters
            window.location.href = `/gallery?date=${date}&time=${encodeURIComponent(time)}&status=${reservation.status}`;
        });
    }
    
    return row;
}

// Function to fetch and display reservations
async function fetchAndDisplayReservations() {
    try {
        const response = await fetch('/get-reservations');
        const data = await response.json();
        
        if (data.status === 'success') {
            const reservationsContainer = document.querySelector('.reservations-container');
            const header = reservationsContainer.querySelector('.reservation-header');
            reservationsContainer.innerHTML = '';
            reservationsContainer.appendChild(header);
            
            // Sort reservations by date and time (newest first)
            const sortedReservations = data.reservations.sort((a, b) => {
                const dateA = new Date(`${a.date} ${a.time}`);
                const dateB = new Date(`${b.date} ${b.time}`);
                return dateB - dateA;
            });
            
            // Add all reservations - let CSS handle the scrolling
            sortedReservations.forEach(reservation => {
                const row = createReservationRow(reservation);
                reservationsContainer.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error fetching reservations:', error);
    }
}

// Function to cancel a reservation
async function cancelReservation(date, time, rowElement) {
    try {
        const response = await fetch('/cancel-reservation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date, time })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Remove the row from the UI
            rowElement.remove();
        } else {
            alert('Failed to cancel reservation: ' + data.message);
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        alert('An error occurred while cancelling the reservation');
    }
}