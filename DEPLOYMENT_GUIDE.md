## Deployment & Maintenance Guide

### Part A: First-Time Production Deployment

1. Prerequisites

- Ubuntu 22.04 server
- Tools: Git, Docker, Docker Compose, Nginx, Certbot
  - `sudo apt update && sudo apt install -y git docker.io docker-compose nginx certbot python3-certbot-nginx`
  - `sudo systemctl enable --now docker`

2. Server Setup

- Create a non-root user and add to docker group:
  - `sudo adduser deploy && sudo usermod -aG docker deploy`
- Firewall (UFW):
  - `sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable`

3. Clone & Configure

- `cd /opt && sudo git clone <your-repo-url> update-data-scraper && sudo chown -R deploy:deploy update-data-scraper`
- `cd update-data-scraper`
- Create `.env` from example:

```
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json

# Postgres
DB_USER=exam_user
DB_PASSWORD=strong_password_here
DB_NAME=exam_updates
# DATABASE_URL is composed in docker-compose using above vars

# AI Keys (optional)
OPENAI_API_KEY=
CLAUDE_API_KEY=
GEMINI_API_KEY=

# Notifications (optional)
NOTIFICATION_WEBHOOK_URL=
NOTIFICATION_WEBHOOK_SECRET=
```

4. Build & Run

- `docker-compose up --build -d`
- App available on port 80 through Nginx.

5. Database Initialization

- Tables auto-create at startup via SQLAlchemy `create_all`. If you need to run a one-time job:
  - `docker-compose exec app python -c "from data.storage import DataStorage; DataStorage().init_database(); print('DB ready')"`

6. Nginx & HTTPS

- The compose loads `nginx.conf`. Point DNS to your server.
- Issue SSL with certbot:
  - `sudo certbot --nginx -d your.domain.com`

7. Auto-Start on Reboot

- Docker services restart policy is set to `unless-stopped`. For an additional systemd unit:

```
sudo tee /etc/systemd/system/exam-updates.service > /dev/null <<'UNIT'
[Unit]
Description=Exam Updates Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/update-data-scraper
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
UNIT
```

- `sudo systemctl enable --now exam-updates`

### Part B: Ongoing Maintenance & Operations

1. Updating the Application

- `cd /opt/update-data-scraper`
- `git pull`
- `docker-compose up --build -d`

2. Database Backups & Restoration

- Create backup script `/opt/update-data-scraper/backup_db.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=${1:-/opt/db_backups}
mkdir -p "$BACKUP_DIR"
docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/exam_updates_$STAMP.sql.gz"
echo "Backup written to $BACKUP_DIR/exam_updates_$STAMP.sql.gz"
```

- Make executable: `chmod +x backup_db.sh`
- Cron job (daily at 02:00): `crontab -e`

```
0 2 * * * /opt/update-data-scraper/backup_db.sh /opt/db_backups >> /var/log/exam_backup.log 2>&1
```

- Restore from backup:

```bash
gunzip -c /opt/db_backups/exam_updates_YYYYMMDD_HHMMSS.sql.gz | docker-compose exec -T db psql -U "$DB_USER" "$DB_NAME"
```

3. Monitoring & Logging

- View app logs: `docker-compose logs -f app`
- Nginx logs are in container: `docker-compose logs -f nginx`
- Check services: `docker-compose ps`

4. Troubleshooting

- 502 Bad Gateway: Ensure app is healthy `docker-compose logs app`; check Nginx config and healthcheck.
- DB connection issues: Verify `DB_*` vars and that `db` container is healthy; confirm `DATABASE_URL` env expansion in `docker-compose.yml`.
- Container crashes: `docker-compose logs <service>`; look for Python tracebacks and fix env/config.

