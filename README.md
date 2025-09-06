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
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Email Notifications (Disabled - focusing on data scraping only)

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
python main.py --mode server --port 5000

# Run single scraping cycle
python main.py --mode single-run

# Run web interface only
python main.py --mode web --port 5000
```

### Web Dashboard

Access the web dashboard at `http://localhost:5000` to:

- View real-time system status
- Monitor recent updates
- Trigger manual scraping
- Manage website configurations
- View scraping statistics
- **Demo Notification System**: Add and manage notifications in real-time

## 🎯 Demo System Workflow

The demo system provides a complete end-to-end example of how the notification system works:

> 📖 **For detailed step-by-step instructions, see [DEMO.md](DEMO.md)**

### Quick Demo Start

### Step-by-Step Demo Process

1. **Start the Demo System**

   ```bash
   # Option 1: Use the demo startup script (recommended)
   python start_demo.py

   # Option 2: Start manually
   python main.py --mode server
   ```

2. **Access the Dashboard**

   - Open http://localhost:5000
   - Scroll down to the "Demo Notification System" section

3. **Initialize the System**

   - Click "Initialize Notifications" button
   - This sets up the notification system and creates data files

4. **Add Demo Notifications**

   - Use the embedded demo interface to add notifications
   - Fill in title, content, exam type, source, priority, URL, and date
   - Click "Add Notification" - this saves to `demo_notifications.json`

5. **Run the Scraper**

   - Click "Run Scrape" button in the dashboard
   - The `DemoScraper` reads from `demo_notifications.json`
   - New notifications are saved to the SQLite database

6. **View Results**
   - New notifications appear in the dashboard
   - Real-time statistics update
   - Toast notifications show new items

### How the Demo System Works

1. **User Input**: Users add notifications via the demo HTML interface
2. **Data Storage**: Notifications are saved to `demo_notifications.json`
3. **Scraper Processing**: `DemoScraper` reads the JSON file and extracts notifications
4. **Database Integration**: New notifications are saved to the SQLite database
5. **Real-time Display**: Dashboard shows all notifications from the database
6. **Live Updates**: Changes are reflected immediately in the dashboard

### API Endpoints

- `GET /status` - System status and statistics
- `GET /recent_updates/<hours>` - Recent updates (default: 24 hours)
- `GET /updates/source/<source>` - Updates from specific source
- `GET /updates/importance/<importance>` - Updates by importance level
- `POST /scrape` - Trigger manual scraping
- `GET /websites` - List configured websites
- `POST /websites/<name>/toggle` - Enable/disable website

## 📁 Project Structure

```
Kapp-Data-Scraper/
├── config/
│   ├── settings.py          # Configuration settings
│   └── websites.json        # Website configurations
├── scrapers/
│   ├── base_scraper.py      # Base scraper class
│   ├── nta_scraper.py       # NTA JEE Main scraper
│   ├── jee_advanced_scraper.py
│   ├── gate_scraper.py      # GATE scraper
│   ├── upsc_scraper.py      # UPSC scraper
│   └── demo_scraper.py      # Demo scraper for testing
├── data/
│   ├── storage.py           # Database management
│   ├── notification_manager.py  # Notification system
│   ├── exam_data.json       # Main data file
│   └── exam_updates.db      # SQLite database
├── mcp_server/
│   ├── server.py            # Main server logic
│   └── scheduler.py         # Scheduling system
├── templates/
│   └── dashboard.html       # Web dashboard
├── utils/
│   ├── helpers.py           # Utility functions
│   └── logger.py            # Logging utilities
├── demo_notifications.html  # Demo notification interface
├── demo_notifications.json  # Demo data storage
├── demo_server.py           # Demo HTTP server
├── main.py                  # Main application entry point
├── start.py                 # Alternative startup script
├── start_demo.py            # Demo system startup script
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── DEMO.md                 # Step-by-step demo guide
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

- [x] Data scraping and storage
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Machine learning for content classification
- [ ] Multi-language support

---

**Note**: This system is designed for educational and informational purposes. Please respect website terms of service and implement appropriate rate limiting.
