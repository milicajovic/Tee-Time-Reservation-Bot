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
            const options = [
                { value: 'exact', text: 'Exact' },
                { value: '12min', text: '±12 min' },
                { value: '24min', text: '±24 min' },
                { value: '36min', text: '±36 min' },
                { value: '1hr', text: '±1 hr' },
                { value: '2hr', text: '±2 hr' },
                { value: '3hr', text: '±3 hr' },
                { value: '4hr', text: '±4 hr' },
                { value: '5hr', text: '±5 hr' }
            ];

            slot.innerHTML = `
                <div class="time-text">${time}</div>
                <div class="time-slot-dropdown">
                    ${options.map(opt => `
                        <div class="time-slot-dropdown-option" data-value="${opt.value}">${opt.text}</div>
                    `).join('')}
                </div>
            `;
            
            let activeDropdown = null;
            let activeSlot = null;

            // Function to update dropdown position
            function updateDropdownPosition() {
                if (activeSlot && activeDropdown) {
                    const rect = activeSlot.getBoundingClientRect();
                    activeDropdown.style.left = `${rect.left}px`;
                    activeDropdown.style.top = `${rect.bottom + 1}px`;
                    // Match dropdown width to time slot width
                    activeDropdown.style.width = `${rect.width}px`;
                    activeDropdown.style.maxWidth = `${rect.width}px`;
                }
            }

            // Add click event listener for the time slot
            slot.addEventListener('click', (e) => {
                // Don't toggle if clicking the dropdown options
                if (e.target.classList.contains('time-slot-dropdown-option')) {
                    return;
                }
                
                const dropdown = slot.querySelector('.time-slot-dropdown');
                
                // If clicking the same active slot, close the dropdown and return
                if (slot.classList.contains('active') && dropdown.style.display === 'block') {
                    dropdown.style.display = 'none';
                    activeDropdown = null;
                    activeSlot = null;
                    return;
                }
                
                // Remove active class from all slots
                document.querySelectorAll('.time-slot').forEach(el => {
                    el.classList.remove('active');
                    // Hide all other dropdowns
                    const otherDropdown = el.querySelector('.time-slot-dropdown');
                    if (otherDropdown) {
                        otherDropdown.style.display = 'none';
                    }
                });
                
                // Add active class to clicked slot
                slot.classList.add('active');
                
                // Store selected time
                selectedTime = time;
                
                // Position and show the dropdown
                activeDropdown = dropdown;
                activeSlot = slot;
                updateDropdownPosition();
                dropdown.style.display = 'block';
            });

            // Add scroll and resize listeners
            window.addEventListener('scroll', updateDropdownPosition, true);
            window.addEventListener('resize', updateDropdownPosition);

            // Handle dropdown option clicks
            const dropdownOptions = slot.querySelectorAll('.time-slot-dropdown-option');
            dropdownOptions.forEach(option => {
                option.addEventListener('click', (e) => {
                    // Clear selected class from ALL options in ALL dropdowns
                    document.querySelectorAll('.time-slot-dropdown-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    
                    // Add selected class to clicked option
                    e.target.classList.add('selected');
                    
                    // Store the selected time range
                    const timeRange = e.target.dataset.value;
                    console.log(`Selected time range for ${time}: ${timeRange}`);

                    // Remove active class from all other time slots
                    document.querySelectorAll('.time-slot').forEach(el => {
                        if (el !== slot) {
                            el.classList.remove('active');
                        }
                    });

                    // Close the dropdown after selection
                    const dropdown = slot.querySelector('.time-slot-dropdown');
                    dropdown.style.display = 'none';
                    if (activeSlot === slot) {
                        activeDropdown = null;
                        activeSlot = null;
                    }
                });
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!slot.contains(e.target)) {
                    // Only hide the dropdown, don't remove the active class
                    const dropdown = slot.querySelector('.time-slot-dropdown');
                    dropdown.style.display = 'none';
                    if (activeSlot === slot) {
                        activeDropdown = null;
                        activeSlot = null;
                    }
                }
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
            // Add loading state to the button
            confirmBtn.classList.add('loading');
            confirmBtn.disabled = true;
            
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
                
                // Remove loading state
                confirmBtn.classList.remove('loading');
                confirmBtn.disabled = false;
                
                if (result.status === 'success') {
                    alert('Reservation submitted successfully!');
                    modal.style.display = 'none';
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
            window.open(reservation.screenshot_folder_url, '_blank');
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