from seleniumbase import SB
import os
from dotenv import load_dotenv
import time
from selenium.webdriver.common.by import By
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from datetime import datetime
import logging
from .blob_storage import BlobStorageService
import random
import pytz
import ntplib
from .attempt_logger import AttemptLogger

# Load environment variables
load_dotenv()

# Initialize blob storage service
blob_service = BlobStorageService()

# Initialize screenshot counter
_screenshot_counter = 0

def take_screenshot(sb, method_name):
    """Helper function to take and save screenshots with sequential numbering"""
    global _screenshot_counter
    _screenshot_counter += 1
    
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots', 'temp')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Generate timestamp and filename with counter
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{_screenshot_counter:03d}_{method_name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        # Take and save screenshot
        sb.save_screenshot(filepath)
        logging.info(f"Screenshot saved temporarily: {filepath}")

        # Upload to Blob Storage
        try:
            blob_service.upload_screenshot(filepath, f"{_screenshot_counter:03d}_{method_name}")
            # Remove local file after successful upload
            os.remove(filepath)
            logging.info(f"Local file removed: {filepath}")
        except ValueError as e:
            logging.error(f"Failed to upload screenshot - no active reservation context: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        logging.error(f"Failed to save or upload screenshot: {str(e)}")

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
    
    # wait for the DOM to render, then a human‐like pause:
    time.sleep(random.uniform(1.2, 2.5))

    selector = ".member-login-large"
    
    for attempt in range(max_attempts):
        manage_tabs(sb)  # Ensure we're on the right tab        
        
        try:
            # Wait for element to be present and visible
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(selector):
                print(f"Found login element with selector: {selector}")
                take_screenshot(sb, "found_login_element")
                # Try different click methods
                try:
                    sb.click(selector)
                    take_screenshot(sb, "after_login_click")
                except:
                    continue
                
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                return True
        except Exception as e:
            print(f"Failed to click {selector}: {str(e)}")
            take_screenshot(sb, "click_member_login")
            continue
    
    if attempt < max_attempts - 1:
        print(f"Click attempt {attempt + 1} failed, refreshing page...")
        sb.refresh()
        time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
    
    return False

def handle_login(sb, max_attempts=3):
    """Handle the login process by entering credentials and clicking sign in"""
    for attempt in range(max_attempts):
        try:
            print("Attempting to log in...")
            
            # wait for the DOM to render, then a human‐like pause:
            time.sleep(random.uniform(1.2, 2.5))
            
            # Verify we're on the login page
            current_url = sb.get_current_url()
            print(f"\nReached login page: {current_url}")
            
            if '/login' not in current_url:
                print("Failed to reach login page")
                take_screenshot(sb, "handle_login")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Wait for username field and enter credentials
            username_selector = "#_58_login"
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(username_selector):
                sb.type(username_selector, LOGIN_CREDENTIALS["username"])
                take_screenshot(sb, "after_username_entered")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for password field and enter credentials
            password_selector = "#_58_password"
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(password_selector):
                sb.type(password_selector, LOGIN_CREDENTIALS["password"])
                take_screenshot(sb, "after_password_entered")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Click the sign in button
            sign_in_selector = "button.btn-sign-in"
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(sign_in_selector):
                sb.click(sign_in_selector)
                take_screenshot(sb, "after_sign_in_click")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the login process
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Verify we're logged in (URL should change)
            current_url = sb.get_current_url()
            if '/login' not in current_url:
                print("Successfully logged in!")
                take_screenshot(sb, "login_successful")
                return True
                
            if attempt < max_attempts - 1:
                print(f"Login attempt {attempt + 1} failed. Retrying...")
                sb.refresh()
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                
        except Exception as e:
            print(f"Login attempt {attempt + 1} failed with error: {str(e)}")
            take_screenshot(sb, "handle_login")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                
    return False

def click_fore_tees(sb, max_attempts=3):
    """Click the Fore Tees link and handle the new tab"""
    fore_tees_link = "a[href*='fore-tees']"
    
    for attempt in range(max_attempts):
        try:
            print("Waiting for home page to load...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Verify we're on the correct page
            current_url = sb.get_current_url()
            if "group/pages/home" not in current_url:
                print(f"Unexpected URL: {current_url}")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            print("Attempting to click Fore Tees link...")
            take_screenshot(sb, "found_fore_tees_link")
            
            # Store the current window handle
            main_window = sb.driver.current_window_handle
            initial_handles = set(sb.driver.window_handles)
            
            # Try to click using JavaScript
            try:
                sb.js_click(fore_tees_link)
                take_screenshot(sb, "after_fore_tees_click")      
            except Exception as e:
                print(f"JavaScript click failed: {str(e)}")
                take_screenshot(sb, "click_fore_tees")
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
                    take_screenshot(sb, "new_tab_opened")
                    print("Successfully switched to Fore Tees tab")
                    
                    # Wait for ForeTees login page to load
                    start_time_inner = time.time()
                    while time.time() - start_time_inner < 10:
                        current_url = sb.get_current_url()
                        if "foretees.com/v5/servlet/Login" in current_url:
                            print(f"Confirmed ForeTees login page loaded: {current_url}")
                            take_screenshot(sb, "foretees_page_loaded")
                            return True
                        time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            print("New tab not detected")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            
        except Exception as e:
            print(f"Error clicking Fore Tees link: {str(e)}")
            take_screenshot(sb, "click_fore_tees")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
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
            take_screenshot(sb, "handle_foretees_navigation")
            return False

        # Wait for Alex Western button
        print("Waiting for Alex Western button...")
        alex_button = "a.standard_button[alt='Alex Western']"
        time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
        if sb.is_element_present(alex_button):
            # Store current tab handle to maintain focus
            foretees_handle = sb.driver.current_window_handle
            take_screenshot(sb, "before_clicking_Alex_Western_button")
            # Click Alex Western button
            print("Clicking Alex Western button...")
            sb.click(alex_button)
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
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
                    take_screenshot(sb, "after_clicking_Alex_Western_button")
                    break
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            else:
                print(f"Timeout waiting for Member page. Current URL: {current_url}")
                return False
                
            # Give the page time to fully load
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            take_screenshot(sb, "waiting_for_continue_button")
            print("Hover over the parent element using SeleniumBase's hover")
            parent_selector = "a[href='#'] span.topnav_item:contains('Tee Times')"
            sb.hover(parent_selector)  # Built-in hover method
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            print("Wait for dropdown to become visible")
            dropdown_xpath = "//a[@href='Member_select']/span[contains(., 'Make, Change, or View Tee Times')]"
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(dropdown_xpath):
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                
                print("Clicking Make, Change, or View Tee Times...")   
                
                take_screenshot(sb, "before_clicking_Make_Change_or_View_Tee_Times")     
                sb.click_xpath(dropdown_xpath)
                take_screenshot(sb, "after_clicking_Make_Change_or_View_Tee_Times")
                # Wait for navigation to complete
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                
                return True
            else:
                print("Dropdown element not found")
                return False
       
    except Exception as e:
        print(f"Error in ForeTees navigation: {str(e)}")
        take_screenshot(sb, "handle_foretees_navigation")
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
            take_screenshot(sb, "found_date_picker")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Find the specific date and check if it's available
            # The date element must have:
            # - ft_code_1 class (indicating it's available)
            # - Correct month (0-based) and year
            date_selector = f"td.ft_code_0[data-month='{month}'][data-year='{year}'] a:contains('{day}')"
            print(f"Checking if {date_str} is available for booking...")
            
            # Wait for the date element to be present and check if it's available
            if not sb.is_element_present(date_selector):
                print("Date is not yet available for booking. Waiting...")
                take_screenshot(sb, "select_tee_time_date")
                if attempt < max_attempts - 1:
                    print(f"Retry attempt {attempt + 1} of {max_attempts}")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Date is available, try to click it
            print("Date is available, attempting to select...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if sb.is_element_present(date_selector):
                sb.click(date_selector)
                take_screenshot(sb, "after_date_selection")
                print(f"Successfully selected {date_str}")
                return True
            
        except Exception as e:
            print(f"Error selecting date (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "select_tee_time_date")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            return False

def select_course(sb, course, max_attempts=3):
    """Select the desired course from the dropdown menu"""
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
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False

            print("Waiting for course dropdown to load...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Find the course dropdown
            course_selector = "select[name='course']"
            if not sb.is_element_present(course_selector):
                print("Course dropdown not found")
                take_screenshot(sb, "course_dropdown_not_found")
                if attempt < max_attempts - 1:
                    print(f"Retry attempt {attempt + 1} of {max_attempts}")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Click the dropdown to open it
            print("Clicking course dropdown...")
            sb.click(course_selector)
            time.sleep(3)
            take_screenshot(sb, "after_course_dropdown_click")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Map the course value to the dropdown option value
            course_value = {
                "Brookhaven": "Brookhaven",
                "Crabapple": "Crabapple",
                "ALL": "-ALL-"
            }.get(course, "-ALL-")  # Default to ALL if course not recognized
            
            # Select the course using SeleniumBase's select_option_by_value
            print(f"Selecting course: {course} (value: {course_value})")
            sb.select_option_by_value(course_selector, course_value)
            time.sleep(2)  # Wait for selection to take effect
            take_screenshot(sb, "after_course_selection")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for URL to update and verify selection by checking URL
            wait_start = time.time()
            url_verified = False
            while time.time() - wait_start < 5:  # Wait up to 5 seconds for URL to update
                current_url = sb.get_current_url()
                print(f"Current URL: {current_url}")
                
                # Check if the course value appears in the URL
                expected_url_param = f"course={course_value}"
                if expected_url_param in current_url:
                    print(f"URL verification successful - found {expected_url_param} in URL")
                    url_verified = True
                    break
                
                time.sleep(0.5)  # Short delay between URL checks
            
            if not url_verified:
                print(f"Warning: Could not verify course selection in URL. Expected {course_value}, URL: {current_url}")
                # Continue anyway since the selection might still have worked
            
            print(f"Successfully selected course: {course} (value: {course_value})")
            return True
            
        except Exception as e:
            print(f"Error selecting course (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "select_course_error")
            if attempt < max_attempts - 1:
                print(f"Retry attempt {attempt + 1} of {max_attempts}")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            return False

def time_to_minutes(time_str):
    """Convert 'HH:MM AM/PM' to minutes since midnight"""
    try:
        dt = datetime.strptime(time_str.upper(), "%I:%M %p")
        return dt.hour * 60 + dt.minute
    except ValueError:
        return None

def wait_until_refresh_time(target_time_est):
    """Precisely wait until target refresh time using server's EST time"""
    while True:
        now = datetime.now(pytz.timezone('America/New_York'))
        if now >= target_time_est:
            break
        # Sleep in small increments near the target time
        delta = (target_time_est - now).total_seconds()
        sleep_time = min(delta, 0.25)  # Check 4x/sec near target time
        time.sleep(sleep_time)
        
class NoSlotWithinRange(Exception):
    """Raised when no tee time slots are available within the allowed range"""
    pass

def select_tee_time(sb, desired_time, time_slot_range, refresh_time_est, logger):
    logger.log(f"START: select_tee_time for {desired_time} (+{time_slot_range})")
    target_min = time_to_minutes(desired_time)
    if target_min is None:
        logger.log("Invalid desired_time format")
        raise ValueError("Invalid desired_time format")
    max_min = target_min + time_slot_range

    fast_xpath = (
        f"//div[contains(@class, 'rwdTr')][.//div[contains(@class, 'slotCount') and "
        f"contains(@class, 'openSlots4')]]//a[contains(@class, 'teetime_button')]"
    )

    logger.log(f"Waiting until {refresh_time_est.strftime('%H:%M:%S')} EST")
    print(f"Waiting until {refresh_time_est.strftime('%H:%M:%S')} EST")
    wait_until_refresh_time(refresh_time_est)
    logger.log("Performing precision refresh")
    refresh_start = time.time()
    # sb.driver.refresh()
    sb.wait_for_element("div.rwdTr", timeout=5)
    refresh_end = time.time()
    logger.log_duration("Refresh and wait_for_element", refresh_start, refresh_end)
    logger.log("Element 'div.rwdTr' found after refresh")

    def get_valid_time_slots():
        slot_search_start = time.time()
        elements = sb.find_elements(fast_xpath, by='xpath')
        logger.log(f"Found {len(elements)} slot elements")
        slots = []
        for el in elements:
            time_str = el.text.strip()
            minutes = time_to_minutes(time_str)
            logger.log(f"Slot element: '{time_str}', parsed minutes: {minutes}")
            if minutes and target_min <= minutes <= max_min:
                slots.append((time_str, minutes))
        slots.sort(key=lambda x: x[1])
        logger.log(f"Valid slots after time filtering: {[s[0] for s in slots]}")
        slot_search_end = time.time()
        logger.log_duration("Slot search", slot_search_start, slot_search_end)
        return slots

    tried_times = set()
    while True:
        valid_slots = get_valid_time_slots()
        logger.log(f"tried_times before filtering: {tried_times}")
        logger.log(f"Valid slots before tried_times filtering: {[s[0] for s in valid_slots]}")
        valid_slots = [slot for slot in valid_slots if slot[0] not in tried_times]
        logger.log(f"Valid slots after tried_times filtering: {[s[0] for s in valid_slots]}")
        if not valid_slots:
            logger.log("No valid slots found, raising NoSlotWithinRange")
            row_xpath = (
                f"//div[contains(@class, 'rwdTr')]"
                f"//*[self::a or self::div[contains(@class, 'time_slot')]]"
                f"[normalize-space(text())='{desired_time}']"
                f"/ancestor::div[contains(@class, 'rwdTr')]"
            )
            parent_row = sb.find_element(row_xpath, by='xpath')            
            sb.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", parent_row)
            take_screenshot(sb, "no_available_slot_at_desired_time")    
            raise NoSlotWithinRange(f"All slots between {desired_time} and {max_min//60}:{max_min%60:02d} were taken or unavailable")
        time_str, minutes = valid_slots[0]
        logger.log(f"About to click slot: {time_str}")
        print(f"Attempting to select time slot: {minutes//60}:{minutes%60:02d}")
        elements = sb.find_elements(fast_xpath, by='xpath')
        target_element = None
        for el in elements:
            if el.text.strip() == time_str:
                target_element = el
                break
        if not target_element:
            logger.log(f"Could not find element for {time_str}, skipping...")
            print(f"Could not find element for {time_str}, skipping...")
            tried_times.add(time_str)
            continue
        click_start = time.time()
        sb.driver.execute_script("arguments[0].click();", target_element)
        click_end = time.time()
        logger.log_duration(f"Click slot {time_str}", click_start, click_end)
        try:
            popup_start = time.time()
            success, status = handle_tee_time_popup(sb, logger=logger)
            popup_end = time.time()
            logger.log_duration(f"handle_tee_time_popup for slot {time_str}", popup_start, popup_end)
            logger.log(f"handle_tee_time_popup result: success={success}, status={status}")
        except Exception as e:
            logger.log(f"Exception in handle_tee_time_popup: {e}")
            print(f"Exception in handle_tee_time_popup: {e}")
            tried_times.add(time_str)
            continue
        if success and status == 'continue':
            logger.log(f"Successfully selected slot {minutes//60}:{minutes%60:02d}")
            logger.log(f"END: select_tee_time")
            return True, f"{minutes//60}:{minutes%60:02d}"
        elif success and status == 'go_back':
            logger.log(f"Time slot {minutes//60}:{minutes%60:02d} was taken, trying next available slot...")
            print(f"Time slot {minutes//60}:{minutes%60:02d} was taken, trying next available slot...")
            tried_times.add(time_str)
            continue
        else:
            logger.log(f"Error handling time slot {minutes//60}:{minutes%60:02d}, trying next available slot...")
            print(f"Error handling time slot {minutes//60}:{minutes%60:02d}, trying next available slot...")
            tried_times.add(time_str)
            continue

def handle_tee_time_popup(sb, logger, max_attempts=3):
    logger.log("START: handle_tee_time_popup")
    for attempt in range(max_attempts):
        attempt_start = time.time()
        try:
            logger.log(f"handle_tee_time_popup attempt {attempt+1}/{max_attempts}")
            logger.log("Waiting for tee time pop-up dialog to appear...")
            wait_start = time.time()
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(".ui-dialog.ui-widget"):
                wait_end = time.time()
                logger.log_duration("Wait for dialog to appear (not found)", wait_start, wait_end)
                print("Dialog not found")
                logger.log("Dialog not found")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    logger.log("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                logger.log("END: handle_tee_time_popup")
                attempt_end = time.time()
                logger.log_duration(f"handle_tee_time_popup attempt {attempt+1}", attempt_start, attempt_end)
                return False, 'error'
            wait_end = time.time()
            logger.log_duration("Wait for dialog to appear (found)", wait_start, wait_end)
            take_screenshot(sb, "popup_appeared")
            button_start = time.time()
            if sb.is_element_present("button:contains('Yes, Continue')"):
                button_end = time.time()
                logger.log_duration("Find 'Yes, Continue' button", button_start, button_end)
                print("Clicking 'Yes, Continue' button...")
                logger.log("Clicking 'Yes, Continue' button...")
                click_start = time.time()
                sb.click("button:contains('Yes, Continue')")
                click_end = time.time()
                logger.log_duration("Click 'Yes, Continue' button", click_start, click_end)
                take_screenshot(sb, "after_popup_handling")
                print("Successfully handled tee time pop-up")
                logger.log("Successfully handled tee time pop-up")
                logger.log("END: handle_tee_time_popup")
                attempt_end = time.time()
                logger.log_duration(f"handle_tee_time_popup attempt {attempt+1}", attempt_start, attempt_end)
                return True, 'continue'
            elif sb.is_element_present("button:contains('Go Back')"):
                button_end = time.time()
                logger.log_duration("Find 'Go Back' button", button_start, button_end)
                print("Found 'Go Back' button - time slot was taken")
                logger.log("Found 'Go Back' button - time slot was taken")
                click_start = time.time()
                sb.click("button:contains('Go Back')")
                click_end = time.time()
                logger.log_duration("Click 'Go Back' button", click_start, click_end)
                take_screenshot(sb, "after_go_back_click")
                logger.log("END: handle_tee_time_popup")
                attempt_end = time.time()
                logger.log_duration(f"handle_tee_time_popup attempt {attempt+1}", attempt_start, attempt_end)
                return True, 'go_back'
            else:
                button_end = time.time()
                logger.log_duration("Find neither button", button_start, button_end)
                print("Neither 'Yes, Continue' nor 'Go Back' button found")
                logger.log("Neither 'Yes, Continue' nor 'Go Back' button found")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    logger.log("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                logger.log("END: handle_tee_time_popup")
                attempt_end = time.time()
                logger.log_duration(f"handle_tee_time_popup attempt {attempt+1}", attempt_start, attempt_end)
                return False, 'error'
        except Exception as e:
            print(f"Error handling tee time pop-up (attempt {attempt + 1}): {str(e)}")
            logger.log(f"Error handling tee time pop-up (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "handle_tee_time_popup")
            if attempt < max_attempts - 1:
                print("Retrying...")
                logger.log("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            logger.log("END: handle_tee_time_popup")
            attempt_end = time.time()
            logger.log_duration(f"handle_tee_time_popup attempt {attempt+1}", attempt_start, attempt_end)
            return False, 'error'

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
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.execute_script("arguments[0].click();", tbd_tab)
            take_screenshot(sb, "found_slot")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the TBD content to be visible
            print(f"Waiting for TBD content for slot {slot_number}...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(".ftMs-block.ftMs-guestTbd.active"):
                print("TBD content not visible")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Click the X element
            print(f"Clicking X element for slot {slot_number}...")
            x_element = sb.find_element(".ftMs-guestTbd .ftMs-listItem span:contains('X')")
            if not x_element:
                print("Could not find X element")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.execute_script("arguments[0].click();", x_element)
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the TBD row to be updated
            print(f"Waiting for TBD row {slot_number} to be updated...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(f"#slot_player_row_{slot_number}.playerTypeGuestTbd"):
                print("TBD row not updated")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Find and click the transport cell in the TBD row
            print(f"Clicking transport cell in TBD row {slot_number}...")
            tbd_transport_cell = sb.find_element(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .ftS-trasportCell")
            if not tbd_transport_cell:
                print(f"Could not find transport cell in TBD row {slot_number}")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.execute_script("arguments[0].click();", tbd_transport_cell)
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the dropdown to be visible and select WLK
            print(f"Selecting WLK from dropdown in TBD row {slot_number}...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .transport_type"):
                print("Transport dropdown not visible")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.select_option_by_text(f"#slot_player_row_{slot_number}.playerTypeGuestTbd .transport_type", "WLK")
            take_screenshot(sb, "after_tbd_set")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            print(f"Successfully set slot {slot_number} as TBD with WLK transport")
            return True
            
        except Exception as e:
            print(f"Error setting slot {slot_number} as TBD (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "set_slot_as_tbd_with_walk")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            return False

def modify_player_slot(sb, max_attempts=3):
    """Modify the first player slot's transport type to WLK and set players as TBD"""
    for attempt in range(max_attempts):
        try:
            print("Waiting for player slots to load...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Find the first player slot row
            first_slot = sb.find_element("#slot_player_row_0")
            if not first_slot:
                print("Could not find first player slot")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            take_screenshot(sb, "found_player_slot")
            
            # Find and click the transport cell
            transport_cell = first_slot.find_element(By.CSS_SELECTOR, ".ftS-trasportCell")
            if not transport_cell:
                print("Could not find transport cell")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Click the transport cell
            print("Clicking transport cell...")
            sb.execute_script("arguments[0].click();", transport_cell)
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the dropdown to be visible and select WLK
            print("Selecting WLK from dropdown...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(".transport_type"):
                print("Transport dropdown not visible")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.select_option_by_text(".transport_type", "WLK")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            # Wait for the member select dialog to appear
            print("Waiting for member select dialog...")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            if not sb.is_element_present(".ftMs-memberSelect"):
                print("Member select dialog not visible")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            
            # Set slots 1, 2, and 3 as TBD with WLK transport
            for slot_number in range(1, 4):  # This will handle slots 1, 2, and 3
                if not set_slot_as_tbd_with_walk(sb, slot_number):
                    print(f"Failed to set slot {slot_number} as TBD")
                    if attempt < max_attempts - 1:
                        print("Retrying...")
                        time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                        continue
                    return False
                # Add a small delay between slots
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            print("Successfully modified all player slots")
            take_screenshot(sb, "after_player_modification")
            
            # Click the Submit Request button
            print("Clicking Submit Request button...")
            submit_button = sb.find_element(".submit_request_button")
            if not submit_button:
                print("Could not find Submit Request button")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False
            sb.execute_script("arguments[0].click();", submit_button)
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            return True
            
        except Exception as e:
            print(f"Error modifying player slot (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "modify_player_slot")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            return False

def handle_confirmation_popup(sb, reservation_time=None, max_attempts=3):
    """Handle the confirmation popup that appears after submitting the request
    Optionally centers the reservation time row and takes a screenshot before final confirmation.
    """
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
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False

            print("Looking for Continue button...")
            # Use XPath to find the Continue button
            button = sb.find_element("//button[.//span[text()='Continue']]")
            
            take_screenshot(sb, "confirmation_popup_appeared")
            
            # Click the button using JavaScript
            print("Clicking Continue button...")
            sb.execute_script("arguments[0].click();", button)

            # Center the reservation time row and take a screenshot before final confirmation
            if reservation_time:
                try:
                    # Universal XPath for any slot state
                    row_xpath = (
                        f"//div[contains(@class, 'rwdTr')]"
                        f"//*[self::a or self::div[contains(@class, 'time_slot')]]"
                        f"[normalize-space(text())='{reservation_time}']"
                        f"/ancestor::div[contains(@class, 'rwdTr')]"
                    )
                    parent_row = sb.find_element(row_xpath, by='xpath')
                except Exception:
                    parent_row = None
                if parent_row:
                    sb.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", parent_row)
                take_screenshot(sb, "time_slots_around_reservation_time")

            take_screenshot(sb, "after_confirmation_handling")
            time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            
            print("Successfully handled confirmation popup")           
            return True
            
        except Exception as e:
            print(f"Error handling confirmation popup (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "handle_confirmation_popup")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
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
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            else:
                print("Could not find Exit link")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False

            # Find and click the RETURN button
            print("Looking for RETURN button...")
            return_button = sb.find_element("//input[@id='submit' and @value='RETURN']")
            if return_button:
                print("Clicking RETURN button...")
                sb.execute_script("arguments[0].click();", return_button)
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
            else:
                print("Could not find RETURN button")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
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
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False

            # Find and click the Logout link
            print("Looking for Logout link...")
            logout_link = sb.find_element("//a[@href='/c/portal/logout']")
            
            take_screenshot(sb, "found_logout_button")
            
            if logout_link:
                print("Clicking Logout link...")
                sb.execute_script("arguments[0].click();", logout_link)
                take_screenshot(sb, "after_logout_click")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                
                # Verify logout
                if "home" in sb.get_current_url():  # or "capitalcityclub.org/web/pages/home"
                    take_screenshot(sb, "logout_successful")
                    return True
            else:
                print("Could not find Logout link")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                    continue
                return False

        except Exception as e:
            print(f"Error during logout process (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, "handle_logout")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(random.uniform(0.8, 1.5))  # Random delay between 800-1500ms
                continue
            return False

def send_email(reservation_date, reservation_time, actual_time=None, success=True):
    sender_email = os.getenv('SENDER_EMAIL')
    app_password = os.getenv('APP_PASSWORD')     
    receiver_emails = os.getenv('RECEIVER_EMAIL').split(',')  # Split by comma to get list of emails
 
    msg = MIMEMultipart()
    msg['Subject'] = "⛳ Reservation Status Update"
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_emails)  # Join emails with commas for display
    
    # Construct the gallery link
    base_url = os.getenv('BASE_URL')  # Get base URL from env or default to localhost
    gallery_link = f"{base_url}/gallery?date={reservation_date}&time={reservation_time}"
    
    if actual_time is not None:       
        hour_str, minute_str = actual_time.split(':')
        hour = int(hour_str)
        minute = int(minute_str)
        
        # Convert to 12-hour format
        period = "AM" if hour < 12 else "PM"
        hour = hour if hour <= 12 else hour - 12
        hour = 12 if hour == 0 else hour  # Handle midnight/noon
        formatted_time = f"{hour}:{minute:02d} {period}"
        
        # Replace actual_time with the formatted version
        actual_time = formatted_time
    

    if success:
        html = f"""<html>
        <body>
            <h3 style="color:#2a5e2a;">Reservation Successful!</h3>
            <p>Your tee time has been booked.</p>
            <p>Date: {reservation_date}<br>
               Time: {actual_time}</p>
            <p>To view the reservation details and screenshots, please <a href="{gallery_link}">click here</a>.</p>
            <p>Thank you for using our service!</p>
        </body>
        </html>"""
    else:
        html = f"""<html>
        <body>
            <h3 style="color:#8b0000;">Reservation Failed</h3>
            <p>We were unable to book your tee time.</p>
            <p>Date: {reservation_date}<br>
               Time: {reservation_time}</p>
            <p>To view the attempt details and screenshots, please <a href="{gallery_link}">click here</a>.</p>
            <p>Please contact support if the issue persists.</p>
            <p>We apologize for any inconvenience.</p>
        </body>
        </html>"""
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_emails, msg.as_string())  # Send to all recipients
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

class TimeSyncError(Exception):
    pass

def verify_time_sync():
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')
    server_time = datetime.fromtimestamp(response.tx_time, pytz.utc)
    local_time = datetime.now(pytz.utc)
    if abs((server_time - local_time).total_seconds()) > 1:
        raise TimeSyncError("Server time out of sync with NTP")

def calculate_refresh_time():
    """
    Calculate the precise refresh time using current date and configured unlock time from .env file.
    
    Returns:
        datetime: Refresh time localized to EST timezone
    """
    # Verify system time is accurate
    verify_time_sync()
    
    # Get unlock time from .env file
    unlock_time_str = os.getenv('UNLOCK_TIME_EST', "07:30")
    print(f"unlock_time_str: {unlock_time_str}")
    
    # Get current date in EST
    est = pytz.timezone('America/New_York')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    
    # Combine current date with configured unlock time
    refresh_time_str = f"{today_str} {unlock_time_str}:00"
    
    # Parse combined datetime
    try:
        naive_refresh_time = datetime.strptime(refresh_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error parsing unlock time: {e}")
        print("Using default unlock time (07:30 EST)")
        naive_refresh_time = datetime.strptime(f"{today_str} 07:30:00", "%Y-%m-%d %H:%M:%S")
    
    # Localize the datetime to EST timezone
    refresh_time = est.localize(naive_refresh_time)
    
    # If refresh_time is in the past (we missed it today), log a warning
    if refresh_time < now_est:
        print(f"WARNING: Unlock time {unlock_time_str} has already passed for today.")
        # We'll still proceed with the operation
    
    # Calculate time difference
    time_diff = (refresh_time - now_est).total_seconds()
    
    # Print debug information about times
    print(f"Target refresh time (EST): {refresh_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    print(f"Current time (EST): {now_est.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    print(f"Time until refresh: {time_diff} seconds")
    
    return refresh_time

def verify_captcha_success(sb, url, max_attempts=3):
    """Verify if the captcha was successfully solved by checking for either:
    1. The presence of the club URL in the current URL
    2. The absence of Cloudflare elements
    Returns True if captcha was solved, False otherwise
    """
    for attempt in range(max_attempts):
        try:
            # Initial connection and captcha handling
            if attempt == 0:
                sb.uc_open_with_reconnect(url, 6)
                take_screenshot(sb, "initial_page_load")
            
            sb.uc_gui_click_captcha()
            take_screenshot(sb, f"after_captcha_attempt_{attempt + 1}")
            
            # Wait for page to stabilize
            time.sleep(random.uniform(1.2, 2.5))                     
                
            # Check for Cloudflare elements
            cloudflare_elements = sb.find_elements("a[href*='cloudflare.com']")
            if not cloudflare_elements:
                print("Captcha verification successful - no Cloudflare elements found")
                take_screenshot(sb, f"no_Cloudflare_element_found_{attempt + 1}")
                return True
                
            print(f"Captcha verification failed - attempt {attempt + 1}")
            if attempt < max_attempts - 1:
                print("Retrying captcha...")
                time.sleep(random.uniform(1.2, 2.5))
                continue
                
            return False
            
        except Exception as e:
            print(f"Error during captcha verification (attempt {attempt + 1}): {str(e)}")
            take_screenshot(sb, f"captcha_verification_error_{attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(1.2, 2.5))
                continue
            return False

def open_website(reservation_date, reservation_time, time_slot_range, course):
    """
    Main function to handle the tee time reservation process.
    When called from app.py, all parameters are required and come from the database.
    """
    # Reset screenshot counter for each attempt
    global _screenshot_counter
    _screenshot_counter = 0

    # Calculate the refresh time using the utility function
    refresh_time = calculate_refresh_time()

    # Get reservation context for logging
    reservation_folder = blob_service.current_reservation_folder
    attempt = blob_service.current_attempt
    logger = AttemptLogger(reservation_folder, attempt, blob_service)

    try:
        url = os.getenv('CLUB_URL')
        logger.log(f"Attempting to navigate to: {url}")
        with SB(uc=True, xvfb=True) as sb:
            with logger.context("verify_captcha_success"):
                if not verify_captcha_success(sb, url):
                    logger.log("Captcha verification failed")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to solve captcha after multiple attempts")
            logger.log("Page loaded successfully. Looking for Member Login link...")
            take_screenshot(sb, "main_page_loaded")
            with logger.context("click_member_login"):
                if not click_member_login(sb):
                    logger.log("Failed to click Member Login link")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to click Member Login link after multiple attempts")
            logger.log("Proceeding with login...")
            with logger.context("handle_login"):
                if not handle_login(sb):
                    logger.log("Failed to complete login process")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to complete login process")
            logger.log("Login successful. Proceeding to Fore Tees...")
            with logger.context("click_fore_tees"):
                if not click_fore_tees(sb):
                    logger.log("Failed to navigate to Fore Tees")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to navigate to Fore Tees")
            logger.log("Proceeding with ForeTees navigation...")
            with logger.context("handle_foretees_navigation"):
                if not handle_foretees_navigation(sb):
                    logger.log("Failed to complete ForeTees navigation")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to complete ForeTees navigation")
            
            # Call the new function to navigate directly to the tee sheet
            logger.log(f"Navigating directly to tee sheet for date: {reservation_date}, course: {course}")
            with logger.context("navigate_to_tee_sheet"):
                if not navigate_to_tee_sheet(sb, reservation_date, course):
                    # Detailed logging and screenshots are handled within navigate_to_tee_sheet
                    logger.log(f"Failed to navigate directly to tee sheet for date: {reservation_date}, course: {course}. Check previous logs for details.")
                    send_email(reservation_date, reservation_time, success=False) # Consistent with other failure emails
                    raise Exception(f"Failed to navigate directly to tee sheet. Date: {reservation_date}, Course: {course}")
            logger.log("Successfully navigated to tee sheet.")
            time.sleep(random.uniform(1.0, 2.0)) # Pause for page to settle after navigation

            logger.log("Proceeding with tee time selection...")
            try:
                with logger.context("select_tee_time"):
                    success, actual_time = select_tee_time(sb, reservation_time, time_slot_range, refresh_time, logger)
                if not success:
                    logger.log("Failed to select tee time")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to select tee time")
            except NoSlotWithinRange as e:
                logger.log(f"No available tee times within the allowed range: {str(e)}")
                send_email(reservation_date, reservation_time, success=False)
                raise Exception(f"No available tee times within the allowed range: {str(e)}")
            logger.log("Proceeding with player slot modification...")
            with logger.context("modify_player_slot"):
                if not modify_player_slot(sb):
                    logger.log("Failed to modify player slot")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to modify player slot")
            logger.log("Proceeding with confirmation popup...")
            with logger.context("handle_confirmation_popup"):
                if not handle_confirmation_popup(sb, reservation_time):
                    logger.log("Failed to handle confirmation popup")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to handle confirmation popup")
            logger.log("Proceeding with logout...")
            with logger.context("handle_logout"):
                if not handle_logout(sb):
                    logger.log("Failed to complete logout process")
                    send_email(reservation_date, reservation_time, success=False)
                    raise Exception("Failed to complete logout process")
            logger.log("Successfully completed all navigation steps")
            sb.wait_for_element_present("body", timeout=2)  # Brief pause before closing
            send_email(reservation_date, reservation_time, actual_time, success=True)
    except Exception as e:
        logger.log(f"An error occurred: {str(e)} | Error type: {type(e).__name__}")
        raise
    finally:
        logger.close_and_upload()

# This section is only for testing the script directly
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python login.py <YYYY-MM-DD> <hh:mm [AM|PM]> <time_slot_range> <course>")
        sys.exit(1)

    date_arg = sys.argv[1]
    time_arg = sys.argv[2]
    time_slot_range = int(sys.argv[3])
    course = sys.argv[4]

    open_website(date_arg, time_arg, time_slot_range, course) 
 