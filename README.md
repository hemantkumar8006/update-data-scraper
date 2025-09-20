# Real-Time Exam Update Scraping System

A comprehensive, production-ready system for scraping and monitoring exam updates from major Indian examination websites including JEE Main, JEE Advanced, CAT, GATE, and UPSC.

## 🚀 Features

- **Real-time Scraping**: Automated scraping every 30 minutes (configurable)
- **AI-Powered Analysis**: Content enhancement using OpenAI, Claude, or Gemini
- **Smart Duplicate Detection**: Prevents duplicate entries using content hashing
- **Robust Error Handling**: Exponential backoff, retry logic, and graceful degradation
- **Web Dashboard**: Real-time monitoring and control interface
- **RESTful API**: Complete API for integration with other systems
- **Data Export**: JSON backups and SQLite database storage
- **Scalable Architecture**: Modular design for easy extension

## 📋 Prerequisites

- Python 3.8 or higher
- API keys for AI services (OpenAI, Claude, or Gemini)
- Internet connection for web scraping

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hemantkumar8006/update-data-scraper.git
cd exam_scraper
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Copy the example environment file and configure your API keys:

```bash
cp env.example .env
```

Edit `.env` file with your API keys:

```env
# API Keys (at least one required)
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Email Notifications (Optional)
NOTIFICATION_EMAIL=your_email@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Environment
ENVIRONMENT=development
```

### 5. Initialize Database

```bash
python -c "from data.storage import DataStorage; DataStorage().init_database()"
```

## 🚀 Usage

### Command Line Options

```bash
# Run full server with web interface
python main.py --mode server --port 6000

# Run single scraping cycle
python main.py --mode single-run

# Run web interface only
python main.py --mode web --port 6000
```

### Web Dashboard

Access the web dashboard at `http://localhost:6000` to:

- View real-time system status
- Monitor recent updates
- Trigger manual scraping
- Manage website configurations
- View scraping statistics

### API Endpoints

- `GET /status` - System status and statistics
- `GET /recent_updates/<hours>` - Recent updates (default: 24 hours)
- `GET /updates/source/<source>` - Updates from specific source
- `GET /updates/importance/<importance>` - Updates by importance level
- `POST /scrape` - Trigger manual scraping
- `GET /websites` - List configured websites
- `POST /websites/<name>/toggle` - Enable/disable website
- `POST /backups/cleanup` - Clean up old backup files (keeps 5 most recent)
- `POST /backups/cleanup-all` - Remove all backup files
- `POST /notifications/send-webhook` - Send notifications to chatbot API
- `POST /webhook/test` - Test webhook connectivity

## 📁 Project Structure

```
exam_scraper/
├── config/
│   ├── settings.py          # Configuration settings
│   └── websites.json        # Website configurations
├── scrapers/
│   ├── base_scraper.py      # Base scraper class
│   ├── nta_scraper.py       # NTA JEE Main scraper
│   ├── jee_advanced_scraper.py
│   ├── cat_scraper.py       # CAT IIM scraper
│   ├── gate_scraper.py      # GATE scraper
│   └── upsc_scraper.py      # UPSC scraper
├── ai_processors/
│   ├── base_processor.py    # AI processor with fallback
│   ├── openai_processor.py  # OpenAI integration
│   ├── claude_processor.py  # Claude integration
│   └── gemini_processor.py  # Gemini integration
├── data/
│   └── storage.py           # Database and storage management
├── mcp_server/
│   ├── server.py            # Main server logic
│   └── scheduler.py         # Scheduling system
├── utils/
│   ├── helpers.py           # Utility functions
│   └── logger.py            # Logging utilities
├── tests/                   # Test files
├── logs/                    # Log files
├── data/                    # Database and backups
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ⚙️ Configuration

### Website Configuration

Edit `config/websites.json` to add, remove, or modify websites:

```json
{
  "websites": [
    {
      "name": "JEE Main NTA",
      "url": "https://jeemain.nta.nic.in/",
      "scraper_class": "NTAScraper",
      "selectors": {
        "news_container": ".latest-news, .updates, .notifications",
        "title": "h3, h4, .title",
        "date": ".date, .publish-date",
        "link": "a"
      },
      "keywords": ["jee", "main", "exam", "admit card", "result"],
      "enabled": true,
      "priority": "high"
    }
  ]
}
```

### Scraping Settings

Modify `config/settings.py` to adjust:

- Scraping interval (default: 30 minutes)
- Request timeout (default: 30 seconds)
- Maximum retries (default: 3)
- AI processing batch size
- Database cleanup settings

## 🔧 Advanced Features

### Adding New Websites

1. Create a new scraper class inheriting from `BaseScraper`
2. Add the website configuration to `config/websites.json`
3. Register the scraper in `scrapers/__init__.py`

### Custom AI Processing

Implement custom AI processors by extending the base classes in `ai_processors/`.

### Monitoring and Alerts

The system includes comprehensive logging and monitoring:

- Structured logging with timestamps
- Performance metrics tracking
- Error rate monitoring
- Database health checks

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 6000

CMD ["python", "main.py", "--mode", "server", "--port", "6000"]
```

### Docker Compose

```yaml
version: "3.8"

services:
  exam-scraper:
    build: .
    ports:
      - "6000:6000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_scrapers.py
```

## 🗂️ Backup Management

The system automatically creates backups of `exam_data.json` before each update. To manage backups:

### Automatic Cleanup

- System keeps only the 5 most recent backups
- Old backups are automatically removed during data updates

### Manual Cleanup

```bash
# Keep 5 most recent backups (default)
python cleanup_backups.py

# Keep only 3 most recent backups
python cleanup_backups.py 3

# Remove all backup files
python cleanup_backups.py --all
```

### API Cleanup

```bash
# Clean up old backups via API
curl -X POST http://localhost:6000/backups/cleanup

# Remove all backups via API
curl -X POST http://localhost:6000/backups/cleanup-all
```

## 🤖 Webhook Integration

The system integrates with a chatbot API to send notifications automatically:

### Webhook Configuration

- **URL**: `https://notification-bot-1757186587.loca.lt/webhook/notification`
- **Secret**: `notif_webhook_2025_secure_key_123`
- **Format**: JSON with title, content, notificationType, and metadata

### Dashboard Controls

- **Send to Bot**: Sends all current notifications to the chatbot API
- **Test Webhook**: Tests connectivity and shows subscriber count
- **Real-time Feedback**: Toast notifications show delivery status

### Webhook Payload Format

```json
{
  "title": "JEE Main 2024 Registration Open",
  "content": "Registration for JEE Main 2024 is now open...",
  "notificationType": "exam_updates",
  "metadata": {
    "examName": "JEE Main",
    "examDate": "2024-01-15",
    "priority": "high",
    "source": "NTA"
  }
}
```

### API Usage

```bash
# Send notifications to webhook
curl -X POST http://localhost:6000/notifications/send-webhook

# Test webhook connectivity
curl -X POST http://localhost:6000/webhook/test
```

## 📊 Monitoring

### System Health

The system provides comprehensive monitoring through:

- Web dashboard with real-time statistics
- RESTful API for external monitoring
- Structured logging for log aggregation
- Database health checks

### Performance Metrics

- Scraping success rates
- AI processing performance
- Database operation statistics
- System resource usage

## 🔒 Security Considerations

- API keys are stored in environment variables
- Database connections use parameterized queries
- Input validation and sanitization
- Rate limiting for external API calls
- Secure logging practices

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure API keys are correctly set in `.env` file
2. **Database Errors**: Check database file permissions and disk space
3. **Scraping Failures**: Verify website URLs and selectors are up-to-date
4. **Memory Issues**: Adjust batch sizes in configuration

### Logs

Check logs in the `logs/` directory for detailed error information:

```bash
tail -f logs/scraper.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details

## 🔄 Updates

The system automatically handles:

- Website structure changes (adaptive parsing)
- API rate limits (exponential backoff)
- Network failures (retry logic)
- Database corruption (automatic recovery)

## 📈 Roadmap

- [ ] Email notifications
- [ ] Webhook integrations
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Machine learning for content classification
- [ ] Multi-language support
- [ ] Cloud deployment templates

---

**Note**: This system is designed for educational and informational purposes. Please respect website terms of service and implement appropriate rate limiting.
