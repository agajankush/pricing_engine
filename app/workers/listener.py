import time
import sys
# This is the celery taks that we want to call asynchronously
from app.workers.tasks import recalculate_all_prices
from app.services.cache import get_redis_client_sync

def start_subscriber():
    try:
        r = get_redis_client_sync()
        r.ping() 
        pubsub = r.pubsub()
        CHANNEL = "market_events"
        print("INFO: Redis connection established. Initializing PubSub.")
        sys.stdout.flush() # Force output immediately
        print(f"Starting Pub/Sub subscriber on channel: {CHANNEL}")
        pubsub.subscribe(CHANNEL)
        print(f"INFO: Subscribed successfully to channel: {CHANNEL}.")
        print("INFO: Entering infinite LISTEN loop now...") # <--- Added log for verification
        sys.stdout.flush()
        
        for message in pubsub.listen():
            print(f"INFO: Received message: {message}")
            sys.stdout.flush()
            if message and message['type'] == 'message':
                event_data = message['data']
                if isinstance(event_data, bytes):
                    event_data = event_data.decode('utf-8')
                print(f"Received event: {event_data}")
                from app.workers.celery_app import celery_app
                celery_app.send_task('app.workers.tasks.recalculate_all_prices')
                print("Celery task submitted successfully")
        # ❌ If the script reaches this line, pubsub.listen() returned.
        print("DIAGNOSTIC FAILURE: PubSub listener loop returned unexpectedly.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR during startup: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
    
if __name__ == "__main__":
    print("Starting Listener process...")
    
    try:
        # 1. Wait for stability
        print("INFO: Waiting 15s for service stability.")
        time.sleep(15) 
        
        # 2. Execute the subscription loop. This function should block indefinitely.
        start_subscriber()
        
    except Exception as e:
        # Catch any errors that occur during the minimal startup phase
        print(f"FATAL ERROR during startup: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
        
    # 💡 CRITICAL: If the script reaches the end of start_subscriber() without
    # entering the infinite loop, it will print this message and exit cleanly.
    # The listener loop must NEVER return if successful.
    print("FATAL ERROR: Listener loop exited unexpectedly!", file=sys.stderr)
    sys.exit(1)
