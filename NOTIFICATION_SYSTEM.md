# Notification System Documentation

## Overview

The notification system implements a smart data management workflow that handles incremental updates and notifications for exam data scraping.

## Workflow Steps

### Step 1: Initial Scrape and Setup

- Scrapes all existing data from the database
- Creates `exam_data.json` with all current data
- Clears `updated_notifications.json` (should be empty initially)

### Step 2: Store Data in Database and Generate File

- All scraped data is stored in the SQLite database
- The main data file `exam_data.json` is created/updated with the complete dataset

### Step 3: Create Updated Notifications File

- `updated_notifications.json` is created to represent new notifications
- Initially empty after the first scrape

### Step 4: Next Interval Scrape

- System scrapes for new data
- `updated_notifications.json` is cleared at the start of each cycle

### Step 5: Data Comparison and Update

- New scraped data is compared with existing data using content hashes
- Only truly new items are added to both files
- `exam_data.json` is updated with: existing data + new data
- `updated_notifications.json` contains: only the new data

### Step 6: Continuous Cycle

- Process repeats for each scraping interval
- Each cycle compares new data with previous data
- Only new items appear in notifications file

## File Structure

### exam_data.json

```json
{
  "jee": [...],
  "gate": [...],
  "jee_adv": [...],
  "upsc": [...],
  "total_notification": 150,
  "last_updated": "2025-01-15T10:30:00",
  "last_scrape": "2025-01-15T10:30:00"
}
```

### updated_notifications.json

```json
{
  "jee": [...],
  "gate": [...],
  "jee_adv": [...],
  "upsc": [...],
  "total_new_notifications": 5,
  "last_updated": "2025-01-15T10:30:00",
  "scrape_timestamp": "2025-01-15T10:30:00"
}
```

## Key Features

1. **Duplicate Detection**: Uses content hashes to prevent duplicate entries
2. **Incremental Updates**: Only new data is processed and stored in notifications
3. **Data Persistence**: Main data file contains complete dataset
4. **Automatic Categorization**: Data is automatically categorized by exam type
5. **Backup System**: Automatic backups are created before updates
6. **Error Handling**: Robust error handling and logging

## Usage

### Command Line Interface

```bash
# Initialize the notification system
python data/notification_manager.py --action init

# Check system status
python data/notification_manager.py --action status

# Clear notifications
python data/notification_manager.py --action clear
```

### API Endpoints

```bash
# Initialize notifications
POST /notifications/init

# Get notification status
GET /notifications/status

# Clear notifications
POST /notifications/clear

# Trigger scraping cycle
POST /scrape
```

### Programmatic Usage

```python
from data.notification_manager import NotificationManager
from data.storage import DataStorage

# Initialize
storage = DataStorage()
manager = NotificationManager(storage)

# Initial setup
manager.initial_scrape_and_setup()

# Process new data
new_data = [...]  # Your scraped data
result = manager.process_next_scrape_cycle(new_data)

# Get status
status = manager.get_status()
```

## Demonstration

Run the workflow demonstration:

```bash
python notification_workflow.py
```

This will show you the complete workflow step by step with mock data.

## Integration

The notification system is integrated into the main scraping server:

1. **MCPExamScrapingServer** now includes a `NotificationManager`
2. **Scraping cycles** automatically process data through the notification system
3. **Web interface** includes endpoints for notification management
4. **Automatic processing** happens on each scraping cycle

## Benefits

1. **Efficient**: Only processes new data, not duplicates
2. **Reliable**: Maintains complete data history
3. **Scalable**: Handles large datasets efficiently
4. **User-friendly**: Clear separation between all data and new notifications
5. **Maintainable**: Clean, well-documented code structure

## Error Handling

The system includes comprehensive error handling:

- Database corruption recovery
- File system error handling
- Data validation and sanitization
- Automatic backup creation
- Detailed logging for debugging

## Performance

- Uses content hashes for fast duplicate detection
- Efficient database queries with proper indexing
- Minimal memory usage with streaming processing
- Automatic cleanup of old data
