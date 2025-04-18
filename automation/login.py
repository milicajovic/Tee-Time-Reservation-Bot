from seleniumbase import SB
import os
from dotenv import load_dotenv
import time
from selenium.webdriver.common.by import By
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import sys
from datetime import datetime
import uuid
import logging
from .blob_storage import BlobStorageService

# Load environment variables
load_dotenv()

# Initialize blob storage service
blob_service = BlobStorageService()

def take_error_screenshot(sb, method_name):
    """Helper function to take and save error screenshots with timestamp"""
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots', 'errors')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{method_name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        # Take and save screenshot
        sb.save_screenshot(filepath)
        logging.info(f"Error screenshot saved locally: {filepath}")

        # Upload to Blob Storage
        url = blob_service.upload_screenshot(filepath, method_name)
        if url:
            logging.info(f"Screenshot uploaded to blob storage: {url}")
            # Remove local file after successful upload
            os.remove(filepath)
            logging.info(f"Local file removed: {filepath}")
        else:
            logging.error("Failed to upload screenshot to blob storage")

    except Exception as e:
        logging.error(f"Failed to save or upload error screenshot: {str(e)}")

# Use credentials from .env
LOGIN_CREDENTIALS = {
    "username": os.getenv("CLUB_USERNAME"),
    "password": os.getenv("CLUB_PASSWORD")
}

def manage_tabs(sb):
    """Close any extra tabs and switch to the main tab"""
    try:
        handles = sb.driver.window_handles
        if len(handles) > 1:
            print(f"Found {len(handles)} tabs, cleaning up...")
            main_handle = handles[0]
            for handle in handles[1:]:
                sb.driver.switch_to.window(handle)
                sb.driver.close()
            sb.driver.switch_to.window(main_handle)
    except Exception as e:
        print(f"Error managing tabs: {str(e)}")

def click_member_login(sb, max_attempts=3):
    """Try to find and click the Member Login link"""
    selector = ".member-login-large"
    
    for attempt in range(max_attempts):
        manage_tabs(sb)  # Ensure we're on the right tab        
        
        try:
            # Wait for element to be present and visible
            if sb.wait_for_element_present(selector, timeout=5):
                print(f"Found login element with selector: {selector}")
                # Try different click methods
                try:
                    sb.click(selector)
                except:
                    continue
                
                sb.wait_for_element_present("body", timeout=2)
                return True
        except Exception as e:
            print(f"Failed to click {selector}: {str(e)}")
            take_error_screenshot(sb, "click_member_login")
            continue
    
    if attempt < max_attempts - 1:
        print(f"Click attempt {attempt + 1} failed, refreshing page...")
        sb.refresh()
        sb.wait_for_element_present("body", timeout=3)
    
    return False

def handle_login(sb, max_attempts=3):
    """Handle the login process by entering credentials and clicking sign in"""
    for attempt in range(max_attempts):
        try:
            print("Attempting to log in...")
            
            # Verify we're on the login page
            current_url = sb.get_current_url()
            print(f"\nReached login page: {current_url}")
            
            if '/login' not in current_url:
                print("Failed to reach login page")
                take_error_screenshot(sb, "handle_login")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            
            # Wait for username field and enter credentials
            username_selector = "#_58_login"
            sb.wait_for_element_present(username_selector, timeout=10)
            sb.type(username_selector, LOGIN_CREDENTIALS["username"])
            
            # Wait for password field and enter credentials
            password_selector = "#_58_password"
            sb.wait_for_element_present(password_selector, timeout=5)
            sb.type(password_selector, LOGIN_CREDENTIALS["password"])
            
            # Click the sign in button
            sign_in_selector = "button.btn-sign-in"
            sb.wait_for_element_present(sign_in_selector, timeout=5)
            sb.click(sign_in_selector)
            
            # Wait for the login process
            sb.wait_for_element_present("body", timeout=3)
            
            # Verify we're logged in (URL should change)
            current_url = sb.get_current_url()
            if '/login' not in current_url:
                print("Successfully logged in!")
                return True
                
            if attempt < max_attempts - 1:
                print(f"Login attempt {attempt + 1} failed. Retrying...")
                sb.refresh()
                sb.wait_for_element_present("body", timeout=2)
                
        except Exception as e:
            print(f"Login attempt {attempt + 1} failed with error: {str(e)}")
            take_error_screenshot(sb, "handle_login")
            if attempt < max_attempts - 1:
                sb.wait_for_element_present("body", timeout=2)
                
    return False

def click_fore_tees(sb, max_attempts=3):
    """Click the Fore Tees link and handle the new tab"""
    fore_tees_link = "a[href*='fore-tees']"
    
    for attempt in range(max_attempts):
        try:
            print("Waiting for home page to load...")
            sb.wait_for_element_present("body", timeout=10)
            
            # Verify we're on the correct page
            current_url = sb.get_current_url()
            if "group/pages/home" not in current_url:
                print(f"Unexpected URL: {current_url}")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    sb.wait_for_element_present("body", timeout=2)
                    continue
                return False
            
            print("Attempting to click Fore Tees link...")
            
            # Store the current window handle
            main_window = sb.driver.current_window_handle
            initial_handles = set(sb.driver.window_handles)
            
            # Try to click using JavaScript
            try:
                sb.js_click(fore_tees_link)      
            except Exception as e:
                print(f"JavaScript click failed: {str(e)}")
                take_error_screenshot(sb, "click_fore_tees")
                if attempt < max_attempts - 1:
                    continue
                return False
            
            # Wait for new tab
            print("Waiting for new tab to open...")
            start_time = time.time()
            while time.time() - start_time < 10:
                current_handles = set(sb.driver.window_handles)
                new_handles = current_handles - initial_handles
                if new_handles:
                    # Switch to the new tab
                    new_tab = list(new_handles)[0]
                    sb.driver.switch_to.window(new_tab)
                    print("Successfully switched to Fore Tees tab")
                    
                    # Wait for ForeTees login page to load
                    start_time_inner = time.time()
                    while time.time() - start_time_inner < 10:
                        current_url = sb.get_current_url()
                        if "foretees.com/v5/servlet/Login" in current_url:
                            print(f"Confirmed ForeTees login page loaded: {current_url}")
                            return True
                        sb.wait_for_element_present("body", timeout=1)
                    
                sb.wait_for_element_present("body", timeout=1)
            
            print("New tab not detected")
            if attempt < max_attempts - 1:
                print("Retrying...")
                continue
            
        except Exception as e:
            print(f"Error clicking Fore Tees link: {str(e)}")
            take_error_screenshot(sb, "click_fore_tees")
            if attempt < max_attempts - 1:
                sb.wait_for_element_present("body", timeout=2)
                continue
            
    return False

def handle_foretees_navigation(sb, max_attempts=3):
    """Handle ForeTees login and navigation"""
    try:
        # Make sure we're in the ForeTees tab
        print("Ensuring we're in the ForeTees tab...")
        for handle in sb.driver.window_handles:
            sb.driver.switch_to.window(handle)
            current_url = sb.get_current_url()
            if "foretees.com" in current_url:
                print(f"Found and switched to ForeTees tab: {current_url}")
                break
        else:
            print("Could not find ForeTees tab")
            return False

        # Wait for Alex Western button
        print("Waiting for Alex Western button...")
        alex_button = "a.standard_button[alt='Alex Western']"
        sb.wait_for_element_clickable(alex_button, timeout=15)
        
        # Store current tab handle to maintain focus
        foretees_handle = sb.driver.current_window_handle
        
        # Click Alex Western button
        print("Clicking Alex Western button...")
        sb.click(alex_button)
        
        # Make sure we stay in the ForeTees tab
        sb.driver.switch_to.window(foretees_handle)
        
        # Wait for URL to change to Member_msg or Member_announce
        print("Waiting for page transition after clicking Alex Western...")
        start_time = time.time()
        while time.time() - start_time < 15:  # 15 second timeout
            current_url = sb.get_current_url()
            print(f"Current URL: {current_url}")  # Debug logging
            if "Member_msg" in current_url or "Member_announce" in current_url:
                print(f"Successfully reached page: {current_url}")
                break
            sb.wait_for_element_present("body", timeout=1)
        else:
            print(f"Timeout waiting for Member page. Current URL: {current_url}")
            return False
            
        # Give the page time to fully load
        sb.wait_for_element_present("body", timeout=2)           
        
        print("Hover over the parent element using SeleniumBase's hover")
        parent_selector = "a[href='#'] span.topnav_item:contains('Tee Times')"
        sb.hover(parent_selector)  # Built-in hover method
        sb.wait_for_element_present("body", timeout=1)
        
        print("Wait for dropdown to become visible")
        dropdown_xpath = "//a[@href='Member_select']/span[contains(., 'Make, Change, or View Tee Times')]"
        sb.wait_for_element_visible(dropdown_xpath)
        sb.wait_for_element_present("body", timeout=1)  # Wait for dropdown animation
                
        print("Clicking Make, Change, or View Tee Times...")        
        sb.click_xpath(dropdown_xpath)
        
        # Wait for navigation to complete
        sb.wait_for_element_present("body", timeout=2)
        
        return True
            
       
    except Exception as e:
        print(f"Error in ForeTees navigation: {str(e)}")
        take_error_screenshot(sb, "handle_foretees_navigation")
        return False

def select_tee_time_date(sb, date_str, max_attempts=3):
    """Select the desired date from the tee time calendar"""
    # Parse the date string (format: YYYY-MM-DD)
    year = int(date_str[:4])
    month = int(date_str[5:7]) - 1  # Convert to 0-based month and remove leading zero
    day = int(date_str[8:10])  # This will automatically remove leading zero
    
    for attempt in range(max_attempts):
        try:
            print("Waiting for calendar to load...")
            sb.wait_for_element_present("#member_select_calendar1", timeout=10)
            
            # Find the specific date and check if it's available
            # The date element must have:
            # - ft_code_1 class (indicating it's available)
            # - "Tee Times Available" title
            # - Correct month (0-based) and year
            date_selector = f"td.ft_code_1[title='Tee Times Available'][data-month='{month}'][data-year='{year}'] a:contains('{day}')"
            print(f"Checking if {date_str} is available for booking...")
            
            # Wait for the date element to be present and check if it's available
            if not sb.is_element_present(date_selector):
                print("Date is not yet available for booking. Waiting...")
                take_error_screenshot(sb, "select_tee_time_date")
                if attempt < max_attempts - 1:
                    print(f"Retry attempt {attempt + 1} of {max_attempts}")
                    time.sleep(5)  # Wait 5 seconds before retrying
                    continue
                return False
            
            # Date is available, try to click it
            print("Date is available, attempting to select...")
            sb.wait_for_element_clickable(date_selector, timeout=10)
            sb.click(date_selector)
            print(f"Successfully selected {date_str}")
            return True
            
        except Exception as e:
            print(f"Error selecting date (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "select_tee_time_date")
            if attempt < max_attempts - 1:
                print("Retrying...")
                sb.wait_for_element_present("body", timeout=2)
                continue
            return False

def select_tee_time(sb, desired_time, max_attempts=3):
    """Select the desired tee time from the available slots"""
    for attempt in range(max_attempts):
        try:
            # Ensure we're on the ForeTees tab
            print("Ensuring we're on the ForeTees tab...")
            for handle in sb.driver.window_handles:
                sb.driver.switch_to.window(handle)
                current_url = sb.get_current_url()
                if "foretees.com" in current_url:
                    print(f"Found and switched to ForeTees tab: {current_url}")
                    break
            else:
                print("Could not find ForeTees tab")
                if attempt < max_attempts - 1:
                    print(f"Retry attempt {attempt + 1} of {max_attempts}")
                    time.sleep(5)
                    continue
                return False, None

            print("Waiting for tee time sheet to load...")
            sb.wait_for_element_present("#main > div.member_sheet_table.standard_list_table.rwdCompactible.rwdTable.rwdShowPgInFull > div.rwdTbody", timeout=10)
            
            # Find all rows in the tee time sheet
            rows = sb.find_elements("div.rwdTr")
            print(f"Found {len(rows)} total rows")
            
            # Find all available time slots with exactly 4 open slots
            available_slots = []
            for row in rows:
                try:
                    # Check if this row has a clickable time button
                    time_button = row.find_element(By.CSS_SELECTOR, "a.teetime_button")
                    if not time_button:
                        continue
                        
                    # Check if this row has exactly 4 open slots
                    slot_count = row.find_elements(By.CSS_SELECTOR, ".slotCount.openSlot.openSlots4")
                    if not slot_count:
                        continue
                        
                    # Get the time text
                    time_text = time_button.text.strip()
                    print(f"Found available time slot: {time_text} with 4 open slots")
                    available_slots.append((time_text, time_button, row))  # Now also store the row element
                except:
                    continue
            
            print(f"Found {len(available_slots)} time slots with 4 open slots")
            
            if not available_slots:
                print("No time slots found with 4 open slots")
                if attempt < max_attempts - 1:
                    print(f"Retry attempt {attempt + 1} of {max_attempts}")
                    time.sleep(5)
                    continue
                return False, None
            
            # Convert times to minutes for comparison
            def time_to_minutes(time_str):
                time_str = time_str.upper()
                is_pm = "PM" in time_str
                time_str = time_str.replace(" AM", "").replace(" PM", "")
                hours, minutes = map(int, time_str.split(":"))
                if is_pm and hours != 12:
                    hours += 12
                return hours * 60 + minutes
            
            # First try to find exact match
            desired_time_min = time_to_minutes(desired_time)
            exact_match = None
            closest_time = None
            min_time_diff = float('inf')
            
            for time_text, time_button, row in available_slots:
                current_time_min = time_to_minutes(time_text)
                time_diff = abs(current_time_min - desired_time_min)
                
                if time_diff == 0:
                    exact_match = (time_text, time_button, row)
                    break
                    
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_time = (time_text, time_button, row)
            
            # Select the time
            if exact_match:
                time_text, time_button, row = exact_match
                print(f"Found exact match for desired time: {time_text}")
            else:
                time_text, time_button, row = closest_time
                print(f"Found closest available time: {time_text} (difference: {min_time_diff} minutes from desired time {desired_time})")
            
            # Scroll the row into center view and take a screenshot
            print(f"Taking screenshot of selected time slot: {time_text}")
            sb.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", row)
            time.sleep(1)  # Give the page a moment to settle after scrolling
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots', 'selected_times')
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate timestamp and filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"selected_time_{time_text.replace(':', '')}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Take the screenshot
            sb.save_screenshot(filepath)
            print(f"Screenshot saved: {filepath}")
            
            # Upload to blob storage and set as success screenshot
            success_url = blob_service.upload_screenshot(filepath, "successful_reservation")
            if success_url:
                blob_service.set_success_screenshot(success_url)
                # Remove local file after successful upload
                # os.remove(filepath) ZA SADA POSLE OTKOMENTARISI
                print(f"Local file removed: {filepath}")
            
            # Click the time button using JavaScript
            sb.execute_script("arguments[0].click();", time_button)
            print(f"Successfully selected time: {time_text}")
            
            return True, time_text
            
        except Exception as e:
            print(f"Error selecting tee time (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "select_tee_time")
            if attempt < max_attempts - 1:
                print("Retrying...")
                sb.wait_for_element_present("body", timeout=2)
                continue
            return False, None

def handle_tee_time_popup(sb, max_attempts=3):
    """Handle the pop-up dialog that appears after selecting a tee time"""
    for attempt in range(max_attempts):
        try:
            print("Waiting for tee time pop-up dialog to appear...")
            
            # Wait for the dialog to appear
            sb.wait_for_element_present(".ui-dialog.ui-widget", timeout=10)
            
            # Wait for the "Yes, Continue" button to be present and clickable
            print("Waiting for 'Yes, Continue' button...")
            sb.wait_for_element_clickable("button:contains('Yes, Continue')", timeout=10)
            
            # Click the "Yes, Continue" button
            print("Clicking 'Yes, Continue' button...")
            sb.click("button:contains('Yes, Continue')")
            
            print("Successfully handled tee time pop-up")

            return True
            
        except Exception as e:
            print(f"Error handling tee time pop-up (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "handle_tee_time_popup")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            return False

def set_slot_as_tbd_with_walk(sb, slot_number, max_attempts=3):
    """Helper function to set a specific slot as TBD and set transport to WLK"""
    for attempt in range(max_attempts):
        try:
            # Click the TBD tab
            print(f"Clicking TBD tab for slot {slot_number}...")
            tbd_tab = sb.find_element("div[data-fttab='.ftMs-guestTbd']")
            if not tbd_tab:
                print("Could not find TBD tab")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            sb.execute_script("arguments[0].click();", tbd_tab)
            
            # Wait for the TBD content to be visible
            print(f"Waiting for TBD content for slot {slot_number}...")
            sb.wait_for_element_visible(".ftMs-block.ftMs-guestTbd.active", timeout=5)
            
            # Click the X element
            print(f"Clicking X element for slot {slot_number}...")
            x_element = sb.find_element(".ftMs-guestTbd .ftMs-listItem span:contains('X')")
            if not x_element:
                print("Could not find X element")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            sb.execute_script("arguments[0].click();", x_element)
            
            # Wait for the TBD row to be updated
            print(f"Waiting for TBD row {slot_number} to be updated...")
            sb.wait_for_element_present(f"#slot_player_row_{slot_number}.playerTypeGuestTbd", timeout=10)
            
            # Find and click the transport cell in the TBD row
            print(f"Clicking transport cell in TBD row {slot_number}...")
            tbd_transport_cell = sb.find_element(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .ftS-trasportCell")
            if not tbd_transport_cell:
                print(f"Could not find transport cell in TBD row {slot_number}")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            sb.execute_script("arguments[0].click();", tbd_transport_cell)
            
            # Wait for the dropdown to be visible and select WLK
            print(f"Selecting WLK from dropdown in TBD row {slot_number}...")
            sb.wait_for_element_visible(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .transport_type", timeout=5)
            sb.select_option_by_text(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .transport_type", "WLK")
            
            print(f"Successfully set slot {slot_number} as TBD with WLK transport")
            return True
            
        except Exception as e:
            print(f"Error setting slot {slot_number} as TBD (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "set_slot_as_tbd_with_walk")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            return False

def modify_player_slot(sb, max_attempts=3):
    """Modify the first player slot's transport type to WLK and set players as TBD"""
    for attempt in range(max_attempts):
        try:
            print("Waiting for player slots to load...")
            sb.wait_for_element_present(".rwdTbody.ftS-playerSlots", timeout=10)
            
            # Find the first player slot row
            first_slot = sb.find_element("#slot_player_row_0")
            if not first_slot:
                print("Could not find first player slot")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            
            # Find and click the transport cell
            transport_cell = first_slot.find_element(By.CSS_SELECTOR, ".ftS-trasportCell")
            if not transport_cell:
                print("Could not find transport cell")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            
            # Click the transport cell
            print("Clicking transport cell...")
            sb.execute_script("arguments[0].click();", transport_cell)
            
            # Wait for the dropdown to be visible and select WLK
            print("Selecting WLK from dropdown...")
            sb.wait_for_element_visible(".transport_type", timeout=5)
            sb.select_option_by_text(".transport_type", "WLK")
            
            # Wait for the member select dialog to appear
            print("Waiting for member select dialog...")
            sb.wait_for_element_present(".ftMs-memberSelect", timeout=10)
            
            # Set slots 1, 2, and 3 as TBD with WLK transport
            for slot_number in range(1, 4):  # This will handle slots 1, 2, and 3
                if not set_slot_as_tbd_with_walk(sb, slot_number):
                    print(f"Failed to set slot {slot_number} as TBD")
                    if attempt < max_attempts - 1:
                        print("Retrying...")
                        time.sleep(2)
                        continue
                    return False
                # Add a small delay between slots
                time.sleep(1)
            
            print("Successfully modified all player slots")
            
            # Click the Submit Request button
            print("Clicking Submit Request button...")
            submit_button = sb.find_element(".submit_request_button")
            if not submit_button:
                print("Could not find Submit Request button")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False
            sb.execute_script("arguments[0].click();", submit_button)
            
            return True
            
        except Exception as e:
            print(f"Error modifying player slot (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "modify_player_slot")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            return False

def handle_confirmation_popup(sb, max_attempts=3):
    """Handle the confirmation popup that appears after submitting the request"""
    for attempt in range(max_attempts):
        try:
            # Make sure we're in the ForeTees tab
            print("Ensuring we're in the ForeTees tab...")
            for handle in sb.driver.window_handles:
                sb.driver.switch_to.window(handle)
                current_url = sb.get_current_url()
                if "foretees.com" in current_url:
                    print(f"Found and switched to ForeTees tab: {current_url}")
                    break
            else:
                print("Could not find ForeTees tab")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False

            print("Looking for Continue button...")
            # Use XPath to find the Continue button
            button = sb.find_element("//button[.//span[text()='Continue']]")
            
            # Click the button using JavaScript
            print("Clicking Continue button...")
            sb.execute_script("arguments[0].click();", button)
            
            print("Successfully handled confirmation popup")           
            return True
            
        except Exception as e:
            print(f"Error handling confirmation popup (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "handle_confirmation_popup")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            return False
        
def handle_logout(sb, max_attempts=3):
    """Handle the logout process across multiple pages"""
    for attempt in range(max_attempts):
        try:
            # First, find and click the Exit link in ForeTees
            print("Looking for Exit link in ForeTees...")
            exit_link = sb.find_element("//li[@class='topnav_right_item lastItem']//a[.//span[text()='Exit']]")
            if exit_link:
                print("Clicking Exit link...")
                sb.execute_script("arguments[0].click();", exit_link)
                time.sleep(2)  # Wait for page transition
            else:
                print("Could not find Exit link")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False

            # Find and click the RETURN button
            print("Looking for RETURN button...")
            return_button = sb.find_element("//input[@id='submit' and @value='RETURN']")
            if return_button:
                print("Clicking RETURN button...")
                sb.execute_script("arguments[0].click();", return_button)
                time.sleep(2)  # Wait for tab to close
            else:
                print("Could not find RETURN button")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False

            # Switch back to the first tab (Capital City Club)
            print("Switching to Capital City Club tab...")
            for handle in sb.driver.window_handles:
                sb.driver.switch_to.window(handle)
                current_url = sb.get_current_url()
                if "capitalcityclub.org" in current_url:
                    print(f"Found and switched to Capital City Club tab: {current_url}")
                    break
            else:
                print("Could not find Capital City Club tab")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False

            # Find and click the Logout link
            print("Looking for Logout link...")
            logout_link = sb.find_element("//a[@href='/c/portal/logout']")
            
            if logout_link:
                print("Clicking Logout link...")
                sb.execute_script("arguments[0].click();", logout_link)
                time.sleep(2)  # Wait for logout to complete
                return True
            else:
                print("Could not find Logout link")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return False

        except Exception as e:
            print(f"Error during logout process (attempt {attempt + 1}): {str(e)}")
            take_error_screenshot(sb, "handle_logout")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            return False

def send_email(reservation_date, reservation_time, success=True):
    sender_email = os.getenv('SENDER_EMAIL')
    app_password = os.getenv('APP_PASSWORD')     
    receiver_email = os.getenv('RECEIVER_EMAIL')
 
    msg = MIMEMultipart()
    msg['Subject'] = "⛳ Reservation Status Update"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # Build screenshot links HTML based on success status
    if success:
        success_url = blob_service.get_success_screenshot_url()
        if success_url:
            links_html = f"<h4>Reservation Confirmation:</h4><p><a href='{success_url}'>View Selected Time</a></p>"
        else:
            links_html = "<p>No confirmation screenshot available.</p>"
    else:
        error_urls = blob_service.get_screenshot_urls()
        if error_urls:
            links_html = "<h4>Error Screenshots:</h4>"
            for url in error_urls:
                filename = os.path.basename(url)
                links_html += f'<p><a href="{url}">{filename}</a></p>'
        else:
            links_html = "<p>No error screenshots were captured in this session.</p>"
    
    if success:
        html = f"""<html>
        <body>
            <h3 style="color:#2a5e2a;">Reservation Successful!</h3>
            <p>Your tee time has been booked.</p>
            <p>Date: {reservation_date}<br>
               Time: {reservation_time}</p>
            {links_html}
            <p>Thank you for using our service!</p>
        </body>
        </html>"""
    else:
        html = f"""<html>
        <body>
            <h3 style="color:#8b0000;">Reservation Failed</h3>
            <p>We were unable to book your tee time.</p>
            {links_html}
            <p>Please try again later or contact support if the issue persists.</p>
            <p>We apologize for any inconvenience.</p>
        </body>
        </html>"""
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def open_website(reservation_date, reservation_time):
    try:
        # Start a new session for this run
        blob_service.start_new_session()
        url = os.getenv('CLUB_URL')
        print(f"Attempting to navigate to: {url}")
                
        with SB(uc=True) as sb:
            sb.uc_open_with_reconnect(url, 6)
            sb.uc_gui_click_captcha()
            print("Page loaded successfully. Looking for Member Login link...")
            
            # Try to click the Member Login link
            if not click_member_login(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to click Member Login link after multiple attempts")
            
            print("Proceeding with login...")
            if not handle_login(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to complete login process")
            
            print("Login successful. Proceeding to Fore Tees...")
            if not click_fore_tees(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to navigate to Fore Tees")
            
            print("Proceeding with ForeTees navigation...")
            if not handle_foretees_navigation(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to complete ForeTees navigation")
            
            print("Proceeding with date selection...")
            if not select_tee_time_date(sb, reservation_date):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to select tee time date")
            
            print("Proceeding with tee time selection...")
            success, actual_time = select_tee_time(sb, reservation_time)
            if not success:
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to select tee time")
            
            # Handle the pop-up dialog
            if not handle_tee_time_popup(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to handle tee time pop-up")
            
            # Modify the player slot
            print("Proceeding with player slot modification...")
            if not modify_player_slot(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to modify player slot")
            
            # Handle the confirmation popup
            print("Proceeding with confirmation popup...")
            if not handle_confirmation_popup(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to handle confirmation popup")
            
            # Handle the logout process
            print("Proceeding with logout...")
            if not handle_logout(sb):
                send_email(reservation_date, reservation_time, success=False)
                raise Exception("Failed to complete logout process")
            
            print("Successfully completed all navigation steps")
            sb.wait_for_element_present("body", timeout=2)  # Brief pause before closing
            
            # If we reach here, everything was successful
            send_email(reservation_date, actual_time, success=True)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python login.py <YYYY-MM-DD> <hh:mm [AM|PM]>")
        sys.exit(1)

    date_arg = sys.argv[1]
    time_arg = sys.argv[2]

    open_website(date_arg, time_arg) 
 