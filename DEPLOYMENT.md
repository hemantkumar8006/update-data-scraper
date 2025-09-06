# Deployment Guide

This guide covers different deployment options for the Exam Update Scraping System.

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd exam_scraper
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Initialize Database**
   ```bash
   python -c "from data.storage import DataStorage; DataStorage().init_database()"
   ```

4. **Test System**
   ```bash
   python test_system.py
   ```

5. **Start System**
   ```bash
   python main.py --mode server
   ```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Setup Environment**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Check Status**
   ```bash
   docker-compose ps
   docker-compose logs -f exam-scraper
   ```

4. **Access Dashboard**
   - Web Interface: http://localhost:5000
   - API Status: http://localhost:5000/status

### Using Docker Only

1. **Build Image**
   ```bash
   docker build -t exam-scraper .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name exam-scraper \
     -p 5000:5000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/config:/app/config \
     -e OPENAI_API_KEY=your_key_here \
     exam-scraper
   ```

## ☁️ Cloud Deployment

### AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.medium or larger
   - Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip docker.io docker-compose git
   sudo usermod -aG docker $USER
   ```

3. **Deploy Application**
   ```bash
   git clone <repository-url>
   cd exam_scraper
   cp env.example .env
   # Edit .env with your API keys
   docker-compose up -d
   ```

4. **Setup Nginx (Optional)**
   ```bash
   sudo apt install nginx
   sudo cp nginx.conf /etc/nginx/sites-available/exam-scraper
   sudo ln -s /etc/nginx/sites-available/exam-scraper /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Google Cloud Platform

1. **Create VM Instance**
   ```bash
   gcloud compute instances create exam-scraper \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-medium \
     --tags=http-server,https-server
   ```

2. **Deploy Application**
   ```bash
   # SSH into instance
   gcloud compute ssh exam-scraper
   
   # Follow AWS deployment steps
   ```

### Azure

1. **Create Virtual Machine**
   ```bash
   az vm create \
     --resource-group myResourceGroup \
     --name exam-scraper \
     --image UbuntuLTS \
     --size Standard_B2s \
     --admin-username azureuser \
     --generate-ssh-keys
   ```

2. **Deploy Application**
   ```bash
   # SSH into VM and follow deployment steps
   ```

## 🔧 Production Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key
# OR
CLAUDE_API_KEY=your_claude_api_key
# OR
GEMINI_API_KEY=your_gemini_api_key

# Optional
NOTIFICATION_EMAIL=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Security Considerations

1. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

2. **Database**
   - Use strong file permissions
   - Regular backups
   - Monitor disk space

3. **Network**
   - Use HTTPS in production
   - Implement rate limiting
   - Firewall configuration

### Monitoring

1. **Health Checks**
   ```bash
   curl http://localhost:5000/status
   ```

2. **Log Monitoring**
   ```bash
   tail -f logs/scraper.log
   ```

3. **Resource Monitoring**
   ```bash
   docker stats exam-scraper
   ```

## 📊 Scaling

### Horizontal Scaling

1. **Load Balancer**
   ```nginx
   upstream exam_scrapers {
       server exam-scraper-1:5000;
       server exam-scraper-2:5000;
       server exam-scraper-3:5000;
   }
   ```

2. **Database Scaling**
   - Use external database (PostgreSQL, MySQL)
   - Implement database clustering
   - Use read replicas

### Vertical Scaling

1. **Resource Limits**
   ```yaml
   # docker-compose.yml
   services:
     exam-scraper:
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 4G
   ```

## 🔄 Backup and Recovery

### Automated Backups

1. **Database Backup**
   ```bash
   # Create backup script
   #!/bin/bash
   cp data/exam_updates.db backups/exam_updates_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Configuration Backup**
   ```bash
   tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz config/
   ```

### Recovery

1. **Database Recovery**
   ```bash
   cp backups/exam_updates_YYYYMMDD_HHMMSS.db data/exam_updates.db
   ```

2. **Full System Recovery**
   ```bash
   # Restore from backup
   tar -xzf backups/full_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   ```

2. **Database Issues**
   ```bash
   # Check database integrity
   python -c "from data.storage import DataStorage; print(DataStorage().check_database_integrity())"
   ```

3. **Scraping Failures**
   ```bash
   # Check logs
   grep "ERROR" logs/scraper.log
   ```

4. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats exam-scraper
   ```

### Performance Tuning

1. **Database Optimization**
   ```sql
   VACUUM;
   ANALYZE;
   ```

2. **Scraping Optimization**
   - Adjust batch sizes
   - Implement caching
   - Use connection pooling

## 📈 Monitoring and Alerting

### Prometheus Metrics

1. **Enable Metrics**
   ```python
   from prometheus_client import start_http_server
   start_http_server(8000)
   ```

2. **Grafana Dashboard**
   - Import dashboard configuration
   - Set up alerts
   - Monitor key metrics

### Log Aggregation

1. **ELK Stack**
   ```yaml
   # docker-compose.yml
   services:
     elasticsearch:
       image: elasticsearch:7.14.0
     logstash:
       image: logstash:7.14.0
     kibana:
       image: kibana:7.14.0
   ```

2. **Fluentd**
   ```yaml
   services:
     fluentd:
       image: fluent/fluentd
       volumes:
         - ./fluent.conf:/fluentd/etc/fluent.conf
   ```

## 🔐 Security Hardening

### SSL/TLS

1. **Let's Encrypt**
   ```bash
   certbot --nginx -d yourdomain.com
   ```

2. **Self-Signed Certificate**
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

### Firewall

1. **UFW (Ubuntu)**
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

2. **iptables**
   ```bash
   iptables -A INPUT -p tcp --dport 22 -j ACCEPT
   iptables -A INPUT -p tcp --dport 80 -j ACCEPT
   iptables -A INPUT -p tcp --dport 443 -j ACCEPT
   ```

## 📋 Maintenance

### Regular Tasks

1. **Daily**
   - Check system status
   - Monitor logs
   - Verify scraping success

2. **Weekly**
   - Database cleanup
   - Log rotation
   - Performance review

3. **Monthly**
   - Security updates
   - Backup verification
   - Capacity planning

### Updates

1. **Application Updates**
   ```bash
   git pull origin main
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

2. **Dependency Updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

For additional support, please refer to the main README.md or create an issue in the repository.
