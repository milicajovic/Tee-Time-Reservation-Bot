// Global variables
let currentYear;
let currentMonth;
let selectedDate = null;
let selectedTime = null;
let selectedTimeRange = '0';  // Default to '0' (Exact)
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
                    // RESET to the first page of slots whenever the date changes
                    currentPanel = 0;
                    // Update time slots based on the selected date
                    updateTimeSlots();
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

// Function to handle time slot clicks and panel management
function setupTimeSlots() {
    const timeSlotsContainer = document.querySelector('.time-slots');
    const navButtons = document.querySelectorAll('.time-nav-btn');
    const modal = document.getElementById('confirmationModal');
    const confirmationText = document.getElementById('confirmationText');
    const cancelBtn = document.querySelector('.cancel-btn');
    const confirmBtn = document.querySelector('.modal-footer .confirm-btn');
    const bookNowBtn = document.querySelector('.book-button');
    let selectedTime = null;
    
    // Function to update time slots display
    function updateTimeSlots() {
            
        const timeSlotsContainer = document.querySelector('.time-slots');
        timeSlotsContainer.innerHTML = '';

        // 1) regenerate all slots
        const allTimeSlots = generateTimeSlots();

        // 2) build panels in chunks of N
        const slotsPerPanel = 18;
        panels = [];
        for (let i = 0; i < allTimeSlots.length; i += slotsPerPanel) {
            panels.push(allTimeSlots.slice(i, i + slotsPerPanel));
        }

        // 3) drop any empty panels just in case
        panels = panels.filter(panel => panel.length > 0);

        // 4) if the user was on a now-nonexistent panel, clamp back to last
        if (currentPanel >= panels.length) {
            currentPanel = panels.length - 1;
        }
        panels[currentPanel].forEach(time => {
            const slot = document.createElement('div');
            slot.className = 'time-slot';
            const options = [
                { value: '0', text: 'Exact' },
                { value: '12', text: '±12 min' },
                { value: '24', text: '±24 min' },
                { value: '36', text: '±36 min' },
                { value: '48', text: '±48 min' },
                { value: '60', text: '±1 hr' },
                { value: '120', text: '±2 hr' },
                { value: '180', text: '±3 hr' },
                { value: '240', text: '±4 hr' },
                { value: '300', text: '±5 hr' }
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
                    selectedTimeRange = e.target.dataset.value;
                    console.log(`Selected time range for ${time}: ${selectedTimeRange}`);

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
                        time: selectedTime,
                        time_slot_range: selectedTimeRange
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
                    selectedTime = null;
                    selectedTimeRange = '0';
                    
                    // Remove active class from calendar day
                    const activeDay = document.querySelector('.calendar-day.active');
                    if (activeDay) {
                        activeDay.classList.remove('active');
                    }
                    
                    // Remove active class from time slot
                    const activeTimeSlot = document.querySelector('.time-slot.active');
                    if (activeTimeSlot) {
                        activeTimeSlot.classList.remove('active');
                    }
                    
                    // Reset the time slot dropdown if it's open
                    const dropdown = activeTimeSlot?.querySelector('.time-slot-dropdown');
                    if (dropdown) {
                        dropdown.style.display = 'none';
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
            alert('Please select both a date and time before confirming.');
        }
    });
    
    // Initialize time slots
    updateTimeSlots();
    
    // Make updateTimeSlots available globally
    window.updateTimeSlots = updateTimeSlots;
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