from flask import Flask, render_template, request, jsonify
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import uuid
from automation.login import open_website

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

        # Extract date and time from the request
        date = data.get('date')
        time = data.get('time')

        # Log the received data
        logging.info(f"Received reservation request - Date: {date}, Time: {time}")

        # Calculate utc_activation_time based on the date and time
        # utc_activation_time = calculate_utc_activation_time2(date, time)
        raw_iso = calculate_utc_activation_time2(date, time)
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
            "utc_activation_time": utc_activation_time,
            "status": "pending",  # default status
            "locked_until": datetime(1970, 1, 1, tzinfo=pytz.utc),
            "retry_count": 0                 # Default retry count is 0
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

def calculate_utc_activation_time2(user_date: str, user_time: str) -> str:
    """
    Test version of calculate_utc_activation_time that schedules the booking 2 minutes from now.
    Returns an ISO 8601 formatted string in UTC.
    """
    # Get current time in ET
    et_tz = pytz.timezone("America/New_York")
    now_et = datetime.now(et_tz)
    
    # Add 2 minutes to current time
    activation_et = now_et + timedelta(minutes=1)
    
    # Convert to UTC
    activation_utc = activation_et.astimezone(pytz.utc)
    return activation_utc.isoformat()

# def calculate_utc_activation_time(user_date: str, user_time: str) -> str:
#     """
#     Calculates utc_activation_time based on user input in Eastern Time (ET).
#     Uses the following rules for advancement:
#         Sunday: 3 days,
#         Monday: 3 days,
#         Tuesday: 4 days,
#         Wednesday: 5 days,
#         Thursday: 6 days,
#         Friday: 3 days,
#         Saturday: 3 days.
#     The activation time in ET is set to 07:30:00, then converted to UTC.
#     Returns an ISO 8601 formatted string.
#     """
#     et_tz = pytz.timezone("America/New_York")
#     dt_str = f"{user_date} {user_time}"
#     desired_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
#     desired_et = et_tz.localize(desired_dt)
    
#     days_advance = {
#         6: 3,  # Sunday
#         0: 3,  # Monday
#         1: 4,  # Tuesday
#         2: 5,  # Wednesday
#         3: 6,  # Thursday
#         4: 3,  # Friday
#         5: 3   # Saturday
#     }
#     advance_days = days_advance.get(desired_et.weekday(), 3)
    
#     activation_et = desired_et - timedelta(days=advance_days)
#     activation_et = activation_et.replace(hour=7, minute=30, second=0, microsecond=0)
#     activation_utc = activation_et.astimezone(pytz.utc)
#     return activation_utc.isoformat()


# New route to process pending reservations, similar to your scheduler.py logic.
@app.route('/run-reservation', methods=['GET','POST'])
def run_reservation():
    # Constants
    MAX_RETRIES = 3
    LOCK_DURATION_MINUTES = 5

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
    retry_count = entity.get("retry_count", 0) + 1

    # 2) Lock it right away
    lock_until = datetime.now(pytz.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
    entity["status"]      = "locked"
    entity["locked_until"] = lock_until
    entity["retry_count"] = retry_count
    table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
    logging.info(f"Locked reservation {row_key} until {lock_until}")

    # 3) PROCESS it
    result = {"RowKey": row_key}
    try:
        logging.info(f"Processing reservation {row_key}: {reservation_date} {reservation_time}")
        open_website(reservation_date, reservation_time)
        # If we get here, it succeeded:
        entity["status"]       = "executed"
        entity["locked_until"] = None
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        logging.info(f"Reservation {row_key} executed successfully")
        result["status"] = "executed"

    except Exception as e:
        # On failure: if we still have retries left, keep status = pending
        if retry_count < MAX_RETRIES:
            entity["status"] = "pending"
            result["status"] = "pending"
            logging.warning(f"Reservation {row_key} failed, retry {retry_count}/{MAX_RETRIES}: {e}")
        else:
            entity["status"] = "failed"
            result["status"] = "failed"
            logging.error(f"Reservation {row_key} failed permanently after {retry_count} tries: {e}")

        # Note: we DO NOT clear locked_until here so that no one picks it
        # up again until the original lock expires.
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        result["error"] = str(e)
        result["retry_count"] = retry_count

    return jsonify({"status": "success", "results": [result]}), 200

    
@app.route('/get-reservations', methods=['GET'])
def get_reservations():
    try:
        table_client = get_table_client()
        # Query all reservations, ordered by date and time
        entities = list(table_client.query_entities(
            query_filter="PartitionKey eq 'reservations'",
            select=["date", "time", "status"]
        ))
        
        # Format the entities for the frontend
        formatted_reservations = []
        for entity in entities:
            formatted_reservations.append({
                'date': entity['date'],
                'time': entity['time'],
                'status': entity['status']
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

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True)
