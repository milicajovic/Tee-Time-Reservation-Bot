from flask import Flask, render_template, request, jsonify
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import uuid
from automation.login import open_website
from weather_service import get_daily_weather

# Import the Azure Data Tables client
from azure.data.tables import TableServiceClient, UpdateMode
from azure.core.exceptions import ResourceExistsError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reservation_logs.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

def get_table_client():
    service_client = TableServiceClient.from_connection_string(conn_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
    return service_client.get_table_client(table_name=os.getenv("AZURE_STORAGE_TABLE_NAME"))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Get the JSON data from the request
        data = request.json

        # Extract date, time, time_slot_range, and course from the request
        date = data.get('date')
        time = data.get('time')
        time_slot_range = int(data.get('time_slot_range', '0'))  # Default to 0 if not provided
        course = data.get('course', 'ALL')  # Default to 'ALL' if not provided

        # Log the received data
        logging.info(f"Received reservation request - Date: {date}, Time: {time}, Time Slot Range: {time_slot_range}, Course: {course}")

        # Calculate utc_activation_time based on the date and time
        raw_iso = calculate_utc_activation_time(date, time)
        utc_activation_time = datetime.fromisoformat(raw_iso)   # handles the "+00:00" offset too
        # Prepare a unique RowKey that starts with the activation time (ISO 8601) for proper sorting,
        # appended with a UUID for uniqueness in case of duplicate activation times.
        row_key = f"{date}_{time}"

        # Build the entity to insert
        reservation_entity = {
            "PartitionKey": "reservations", 
            "RowKey": row_key,  # This is a unique identifier for the entity
            "date": date,
            "time": time,
            "time_slot_range": time_slot_range,  # Add the time slot range
            "utc_activation_time": utc_activation_time,
            "status": "pending",  # default status
            "locked_until": datetime(1970, 1, 1, tzinfo=pytz.utc),
            "retry_count": 0,                 # Default retry count is 0
            "screenshot_folder_url": "",     # Will be set when processing starts
            "course": course                  # Use the provided course or default to 'ALL'
        }

        # Insert the entity into the table
        table_client = get_table_client()
        table_client.create_entity(entity=reservation_entity)
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation request received',
            'data': reservation_entity
        })
    except ResourceExistsError:
        # This triggers if the (PartitionKey, RowKey) already exist.
        message = f"A reservation already exists for {date} {time}."
        logging.info(message)
        return jsonify({'status': 'error', 'message': message}), 409
    except Exception as e:
        logging.error(f"Error processing reservation request: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Just for testing
# def calculate_utc_activation_time2(user_date: str, user_time: str) -> str:
#     """
#     Test version of calculate_utc_activation_time that schedules the booking 2 minutes from now.
#     Returns an ISO 8601 formatted string in UTC.
#     """
#     # Get current time in ET
#     et_tz = pytz.timezone("America/New_York")
#     now_et = datetime.now(et_tz)
    
#     # Add 2 minutes to current time
#     activation_et = now_et + timedelta(minutes=1)
    
#     # Convert to UTC
#     activation_utc = activation_et.astimezone(pytz.utc)
#     return activation_utc.isoformat()

def calculate_utc_activation_time(user_date: str, user_time: str) -> str:
    """
    Calculates utc_activation_time based on user input in Eastern Time (ET).
    Uses the following rules for advancement:
        Sunday: 3 days,
        Monday: 3 days,
        Tuesday: 4 days,
        Wednesday: 5 days,
        Thursday: 6 days,
        Friday: 3 days,
        Saturday: 3 days.
    The activation time in ET is set to 07:30:00, then converted to UTC.
    Returns an ISO 8601 formatted string.
    """
    et_tz = pytz.timezone("America/New_York")
    dt_str = f"{user_date} {user_time}"
    desired_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
    desired_et = et_tz.localize(desired_dt)
    
    days_advance = {
        6: 3,  # Sunday
        0: 3,  # Monday
        1: 4,  # Tuesday
        2: 5,  # Wednesday
        3: 6,  # Thursday
        4: 3,  # Friday
        5: 3   # Saturday
    }
    advance_days = days_advance.get(desired_et.weekday(), 3)
    
    activation_et = desired_et - timedelta(days=advance_days)
    activation_et = activation_et.replace(hour=7, minute=26, second=0, microsecond=0)
    activation_utc = activation_et.astimezone(pytz.utc)
    return activation_utc.isoformat()


# New route to process pending reservations, similar to your scheduler.py logic.
@app.route('/run-reservation', methods=['GET','POST'])
def run_reservation():
    # Constants
    MAX_RETRIES = 3
    LOCK_DURATION_MINUTES = 7

    table_client = get_table_client()
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1) Find ONE pending reservation whose activation time has arrived
    #    and whose lock has already expired.
    filter_query = (
        "status eq 'pending' and "
        f"utc_activation_time le datetime'{now_utc}' and "
        f"locked_until lt datetime'{now_utc}'"
    )
    entities = table_client.query_entities(filter_query)
    entity = next(entities, None)

    if not entity:
        logging.info(f"No pending reservations to process at {now_utc}")
        return jsonify({"status": "success", "results": []}), 200

    row_key = entity["RowKey"]
    reservation_date = entity["date"]
    reservation_time = entity["time"]
    time_slot_range = entity.get("time_slot_range", 0)  # Get time_slot_range, default to 0
    course = entity["course"]  # Get course directly from entity
    retry_count = entity.get("retry_count", 0) + 1

    # 2) Lock it right away
    lock_until = datetime.now(pytz.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
    entity["status"] = "locked"
    entity["locked_until"] = lock_until
    entity["retry_count"] = retry_count
    
    # If this is the first attempt (retry_count = 1), generate and store the screenshot folder URL
    if retry_count == 1 and not entity.get("screenshot_folder_url"):
        from automation.login import blob_service
        blob_service.set_reservation_context(row_key, retry_count)
        entity["screenshot_folder_url"] = blob_service.get_reservation_folder_url()
        logging.info(f"Generated screenshot folder URL for reservation {row_key}")
    
    table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
    logging.info(f"Locked reservation {row_key} until {lock_until}")

    # Set up the blob storage context for this reservation
    from automation.login import blob_service
    blob_service.set_reservation_context(row_key, retry_count)

    # 3) PROCESS it
    result = {"RowKey": row_key}
    try:
        logging.info(f"Processing reservation {row_key}: {reservation_date} {reservation_time} with time slot range {time_slot_range} for course {course}")
        open_website(reservation_date, reservation_time, time_slot_range, course)
        # If we get here, it succeeded:
        entity["status"] = "executed"
        entity["locked_until"] = None
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        logging.info(f"Reservation {row_key} executed successfully")
        result["status"] = "executed"

    except Exception as e:
        # On failure: if we still have retries left, keep status = pending
        error_message = str(e)
        if "No available tee times within the allowed range" in error_message:
            # Immediately mark as failed for no available tee times
            entity["status"] = "failed"
            result["status"] = "failed"
            logging.error(f"Reservation {row_key} failed - no available tee times: {error_message}")
        elif retry_count < MAX_RETRIES:
            entity["status"] = "pending"
            result["status"] = "pending"
            logging.warning(f"Reservation {row_key} failed, retry {retry_count}/{MAX_RETRIES}: {error_message}")
        else:
            entity["status"] = "failed"
            result["status"] = "failed"
            logging.error(f"Reservation {row_key} failed permanently after {retry_count} tries: {error_message}")

        # Note: we DO NOT clear locked_until here so that no one picks it
        # up again until the original lock expires.
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        result["error"] = error_message
        result["retry_count"] = retry_count

    return jsonify({"status": "success", "results": [result]}), 200

    
@app.route('/get-reservations', methods=['GET'])
def get_reservations():
    try:
        table_client = get_table_client()
        # Query all reservations, ordered by date and time
        entities = list(table_client.query_entities(
            query_filter="PartitionKey eq 'reservations'",
            select=["date", "time", "status", "retry_count", "screenshot_folder_url"]
        ))
        
        # Format the entities for the frontend
        formatted_reservations = []
        for entity in entities:
            formatted_reservations.append({
                'date': entity['date'],
                'time': entity['time'],
                'status': entity['status'],
                'retry_count': entity.get('retry_count', 0),  # Default to 0 if not present
                'screenshot_folder_url': entity.get('screenshot_folder_url', '')  # Default to empty string if not present
               
            })
        
        return jsonify({
            'status': 'success',
            'reservations': formatted_reservations
        })
    except Exception as e:
        logging.error(f"Error fetching reservations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/cancel-reservation', methods=['POST'])
def cancel_reservation():
    try:
        data = request.json
        date = data.get('date')
        time = data.get('time')
        
        if not date or not time:
            return jsonify({
                'status': 'error',
                'message': 'Date and time are required'
            }), 400
            
        table_client = get_table_client()
        row_key = f"{date}_{time}"
        
        # Delete the entity instead of updating its status
        table_client.delete_entity(partition_key="reservations", row_key=row_key)
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation deleted successfully'
        })
    except Exception as e:
        logging.error(f"Error cancelling reservation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/weather', methods=['GET'])
def weather():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error":"`date` param required"}), 400

    try:
        weather = get_daily_weather(date_str)
        return jsonify(weather)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/gallery')
def gallery():
    date = request.args.get('date')
    time = request.args.get('time')
    status = request.args.get('status') 
    
    # Get screenshots from blob storage
    from automation.login import blob_service
    screenshots = blob_service.get_screenshots(date, time)
    
    # Format date and time for display
    formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')
    formatted_time = time

    if not status:
        status = get_reservation_status(date, time)
    
    return render_template('gallery.html', 
                         date=formatted_date, 
                         time=formatted_time, 
                         screenshots=screenshots,
                         status=status)

@app.route('/blob-image/<path:blob_path>')
def serve_blob_image(blob_path):
    try:
        from automation.login import blob_service
        # Get blob data with cache headers
        blob_data, headers = blob_service.get_blob_with_cache_headers(blob_path)
        return blob_data, 200, headers
    except Exception as e:
        logging.error(f"Error serving blob image: {str(e)}")
        return '', 404
    
def get_reservation_status(date, time):
    table_client = get_table_client()
    row_key = f"{date}_{time}"
    try:
        entity = table_client.get_entity(partition_key="reservations", row_key=row_key)
        return entity.get('status', 'failed')
    except Exception as e:
        # Log the error if needed
        return None
    
if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True)
