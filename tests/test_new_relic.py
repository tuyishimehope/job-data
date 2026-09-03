from datetime import datetime, timezone

from app.infrastructure.observability.new_relic import (
    new_relic_log_client,
)

def main():

    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "New Relic connectivity test",
        "service": "job-ingestion-api",
        "environment": "development",
        "event": "new_relic_test",
        "request_id": "test-123",
    }

    new_relic_log_client.send(log)

    print("sent")
    
if __name__ == "__main__":
    main()