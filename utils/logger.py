import logging
import json
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_FORMAT


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        # Include extra fields if present
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName',
                'process', 'asctime'
            ):
                payload[key] = value
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(log_level: str = LOG_LEVEL, log_format: str = LOG_FORMAT):
    """Setup logging to stdout. JSON format by default for production."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    if (log_format or 'json').lower() == 'json':
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name):
    """Get logger instance"""
    return logging.getLogger(name)


def log_scraping_attempt(logger, source, status, updates_found=0, error_message=None, duration=None):
    """Log scraping attempt with structured information"""
    log_data = {
        'source': source,
        'status': status,
        'updates_found': updates_found,
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_message:
        log_data['error'] = error_message
        logger.error(f"Scraping failed for {source}: {error_message}", extra=log_data)
    else:
        logger.info(f"Scraping completed for {source}: {updates_found} updates found", extra=log_data)


def log_ai_processing(logger, processor_name, updates_count, success_count, error_message=None):
    """Log AI processing results"""
    log_data = {
        'processor': processor_name,
        'total_updates': updates_count,
        'successful_updates': success_count,
        'failed_updates': updates_count - success_count,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_message:
        log_data['error'] = error_message
        logger.error(f"AI processing failed with {processor_name}: {error_message}", extra=log_data)
    else:
        logger.info(f"AI processing completed with {processor_name}: {success_count}/{updates_count} successful", extra=log_data)


def log_database_operation(logger, operation, table, records_affected=0, error_message=None):
    """Log database operations"""
    log_data = {
        'operation': operation,
        'table': table,
        'records_affected': records_affected,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_message:
        log_data['error'] = error_message
        logger.error(f"Database {operation} failed on {table}: {error_message}", extra=log_data)
    else:
        logger.info(f"Database {operation} completed on {table}: {records_affected} records affected", extra=log_data)


def log_system_event(logger, event_type, message, details=None):
    """Log system events"""
    log_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        log_data['details'] = details
    
    if event_type in ['error', 'critical']:
        logger.error(f"System {event_type}: {message}", extra=log_data)
    elif event_type == 'warning':
        logger.warning(f"System warning: {message}", extra=log_data)
    else:
        logger.info(f"System {event_type}: {message}", extra=log_data)


class StructuredLogger:
    """Logger that provides structured logging capabilities"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_scraping_start(self, source, url):
        """Log start of scraping operation"""
        self.logger.info(f"Starting scraping for {source}", extra={
            'source': source,
            'url': url,
            'operation': 'scraping_start',
            'timestamp': datetime.now().isoformat()
        })
    
    def log_scraping_end(self, source, updates_found, duration, status='success'):
        """Log end of scraping operation"""
        self.logger.info(f"Scraping completed for {source}: {updates_found} updates", extra={
            'source': source,
            'updates_found': updates_found,
            'duration': duration,
            'status': status,
            'operation': 'scraping_end',
            'timestamp': datetime.now().isoformat()
        })
    
    def log_ai_processing_start(self, processor_name, updates_count):
        """Log start of AI processing"""
        self.logger.info(f"Starting AI processing with {processor_name}", extra={
            'processor': processor_name,
            'updates_count': updates_count,
            'operation': 'ai_processing_start',
            'timestamp': datetime.now().isoformat()
        })
    
    def log_ai_processing_end(self, processor_name, success_count, total_count):
        """Log end of AI processing"""
        self.logger.info(f"AI processing completed with {processor_name}: {success_count}/{total_count}", extra={
            'processor': processor_name,
            'success_count': success_count,
            'total_count': total_count,
            'operation': 'ai_processing_end',
            'timestamp': datetime.now().isoformat()
        })
    
    def log_database_save(self, table, records_saved):
        """Log database save operation"""
        self.logger.info(f"Saved {records_saved} records to {table}", extra={
            'table': table,
            'records_saved': records_saved,
            'operation': 'database_save',
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, operation, error_message, details=None):
        """Log error with structured information"""
        log_data = {
            'operation': operation,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            log_data['details'] = details
        
        self.logger.error(f"Error in {operation}: {error_message}", extra=log_data)
    
    def log_performance(self, operation, duration, records_processed=None):
        """Log performance metrics"""
        log_data = {
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        if records_processed is not None:
            log_data['records_processed'] = records_processed
        
        self.logger.info(f"Performance: {operation} took {duration:.2f}s", extra=log_data)
