# MyWhoosh2Garmin 🚴‍♂️💨 ➡️ ⌚

Automated sync service that downloads your cycling activities from **MyWhoosh**, enhances the `.fit` files with Garmin Edge device signatures to enable Garmin **Physio TrueUp** (Training Load, Training Effect, VO2 Max, Recovery Time), and uploads them directly to **Garmin Connect**.

Packaged as a lightweight, containerized Docker service suitable for running on home servers, NAS devices (Synology, Unraid, TrueNAS), Raspberry Pis, or any system with Docker.

---

## 🌟 Key Features

* **🔄 Automated Synchronization**: Runs as a set-and-forget background daemon polling MyWhoosh for new rides at configurable intervals (e.g., every 60 minutes).
* **🎯 Garmin Physio TrueUp & Training Metrics**: By default, standard third-party virtual rides uploaded to Garmin Connect do not calculate Training Load or Training Effect. **MyWhoosh2Garmin** patches the FIT file metadata (`FileIdMessage` and `DeviceInfoMessage`) to identify as a **Garmin Edge 1040** (or Edge 840), unlocking full physiological training metrics in Garmin Connect.
* **🛡️ Multi-Tier Duplicate Prevention**:
  1. **Persistent SQLite Store**: Remembers synced activity IDs across reboots and container restarts.
  2. **Garmin Connect Time Window**: Checks Garmin Connect for activities matching within a ±2 hour window (preventing duplicates if you also recorded on your watch/bike computer).
  3. **HTTP 409 Conflict Protection**: Gracefully catches Garmin's upload duplicate response.
* **🔑 Secure Token Caching**: Stores Garmin session tokens inside the `data/garmin_tokens` directory, preventing repetitive 2FA prompts and avoiding account lockouts.
* **🐳 Docker & Docker Compose Ready**: Single-command startup with minimal resource overhead and only a single volume mount (`./data:/data`).
* **🛠️ Flexible CLI Controls**: Supports single-ride sync (`--sync-latest`), batch backfills (`--batch 10`), database inspection (`--status`), and simulations (`--dry-run`).

---

## 🏗️ Architecture

```
┌─────────────────────────┐
│      MyWhoosh API       │
│  - REST Session Auth    │
│  - Activity Discovery   │
│  - S3 Pre-signed URL    │
└────────────┬────────────┘
             │ Raw .fit download
             ▼
┌─────────────────────────┐
│   FIT Device Enhancer   │
│  - fit-tool processor   │
│  - Edge 1040/840 spoof  │
│  - NP / IF / TSS work   │
└────────────┬────────────┘
             │ Enhanced .fit
             ▼
┌─────────────────────────┐
│     Garmin Connect      │
│  - Cached Token Auth    │
│  - Duplicate Checking   │
│  - FIT Binary Upload    │
└────────────┬────────────┘
             │ Upload Confirmation
             ▼
┌─────────────────────────┐
│   SQLite Sync Store     │
│  (/data/sync_state.db)  │
└─────────────────────────┘
```

---

## 🚀 Quick Start with Docker Compose (Recommended)

### 1. Clone the repository

```bash
git clone https://github.com/erwinvol/Mywhoosh2garmin.git
cd Mywhoosh2garmin
```

### 2. Configure Environment Variables in `docker-compose.yml`

Edit `docker-compose.yml` directly under the `environment:` section:

```yaml
services:
  mywhoosh2garmin:
    build: .
    image: mywhoosh2garmin:latest
    container_name: mywhoosh2garmin
    restart: unless-stopped
    ports:
      - "${WEBHOOK_PORT:-8080}:8080"
    environment:
      - MYWHOOSH_EMAIL=your_mywhoosh_email@example.com
      - MYWHOOSH_PASSWORD=your_mywhoosh_password
      - GARMIN_USERNAME=your_garmin_email@example.com
      - GARMIN_PASSWORD=your_garmin_password
      - DATA_DIR=/data
      - GARMIN_TOKEN_DIR=/data/garmin_tokens
      # Sync interval (minutes) - Set to 0 to disable polling and use only Home Assistant webhooks
      - SYNC_INTERVAL_MINUTES=60
      - WEBHOOK_ENABLED=true
      - WEBHOOK_PORT=8080
      - WEBHOOK_TOKEN=your_secret_token
    volumes:
      - ./data:/data
```

> [!NOTE]
> All SQLite activity tracking and Garmin session tokens are self-contained inside the `./data` volume. Only a single volume mount (`./data:/data`) is required!

### 3. Launch with Docker Compose

```bash
docker compose up -d
```

View the logs in real time:

```bash
docker compose logs -f
```

---

## 🐳 Running with Docker CLI

### Build the Image:

```bash
docker build -t mywhoosh2garmin:latest .
```

### Run as a Background Daemon (60m interval):

```bash
docker run -d \
  --name mywhoosh2garmin \
  --restart unless-stopped \
  -e MYWHOOSH_EMAIL="your_email@example.com" \
  -e MYWHOOSH_PASSWORD="your_password" \
  -v $(pwd)/data:/data \
  mywhoosh2garmin:latest
```

### Run a One-Off Sync (Latest Ride):

```bash
docker run --rm \
  -e MYWHOOSH_EMAIL="your_email@example.com" \
  -e MYWHOOSH_PASSWORD="your_password" \
  -v $(pwd)/data:/data \
  mywhoosh2garmin:latest --sync-latest
```

### View Synchronization Status:

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  mywhoosh2garmin:latest --status
```

---

## ⚙️ Configuration Reference

All settings can be configured directly inside `docker-compose.yml`, environment variables, or a `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MYWHOOSH_EMAIL` | **Required** | Your MyWhoosh login email address |
| `MYWHOOSH_PASSWORD` | **Required** | Your MyWhoosh account password |
| `GARMIN_USERNAME` | *Optional* | Your Garmin Connect email (required if tokens are not yet cached) |
| `GARMIN_PASSWORD` | *Optional* | Your Garmin Connect password |
| `DATA_DIR` | `/data` | Directory where SQLite state database and tokens are stored |
| `GARMIN_TOKEN_DIR` | `/data/garmin_tokens` | Directory storing Garmin session tokens (inside `DATA_DIR`) |
| `SYNC_INTERVAL_MINUTES`| `60` | Polling frequency in minutes when in daemon mode (default 60m) |
| `SYNC_BATCH_SIZE` | `10` | Max recent activities to evaluate per cycle |
| `CHECK_DUPLICATES` | `true` | Verify if ride is already in Garmin Connect |
| `DUPLICATE_THRESHOLD_HOURS` | `2` | Matching time window around ride timestamp |
| `SPOOF_GARMIN_DEVICE`| `true` | Patch FIT file with Garmin Edge device signatures |
| `DEVICE_PRODUCT_ID` | `3927` | Garmin Device ID (`3927` = Edge 1040, `4024` = Edge 840) |
| `DEVICE_SOFTWARE_VERSION` | `27.10` | Device firmware version reported in FIT header |
| `ATHLETE_FTP` | `0` | Optional FTP wattage for Normalized Power / TSS calculations |
| `WEBHOOK_ENABLED` | `true` | Enable lightweight HTTP webhook server for on-demand triggers |
| `WEBHOOK_PORT` | `8080` | Port for the webhook server |
| `WEBHOOK_HOST` | `0.0.0.0` | Bind host for the webhook server |
| `WEBHOOK_TOKEN` | *(empty)* | Secret bearer token for authenticating webhook requests |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 🏠 Home Assistant On-Demand Webhook Trigger

To eliminate unnecessary periodic API polling against MyWhoosh and Garmin, you can trigger a synchronization on-demand (e.g., when your indoor ride or smart trainer powers off).

### 1. Configure MyWhoosh2Garmin
In your `.env` or `docker-compose.yml`:
```bash
# Set polling to 0 to disable timed API pings
SYNC_INTERVAL_MINUTES=0

# Configure webhook listener
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8080
WEBHOOK_TOKEN=your_secure_webhook_token_here
```

### 2. Configure Home Assistant (`secrets.yaml` & `configuration.yaml`)

In `secrets.yaml`:
```yaml
mywhoosh_webhook_token: "your_secure_webhook_token_here"
```

In `configuration.yaml`:
```yaml
rest_command:
  trigger_mywhoosh_sync:
    url: "http://<mywhoosh2garmin-host-ip>:8080/sync"
    method: POST
    headers:
      X-Webhook-Token: "!secret mywhoosh_webhook_token"
    timeout: 30
```

*(Optional)* Monitor MyWhoosh2Garmin health/status with a REST sensor in Home Assistant:
```yaml
sensor:
  - platform: rest
    name: "MyWhoosh2Garmin Status"
    resource: "http://<mywhoosh2garmin-host-ip>:8080/health"
    value_template: "{{ value_json.status }}"
    json_attributes:
      - is_syncing
      - last_sync_time
      - uptime_seconds
    scan_interval: 300
```

### 3. Home Assistant Automation Example (Smart Trainer Power Sensing)

Trigger when your smart trainer plug reports power dropping below 15W for 2 minutes after a workout:

```yaml
alias: "MyWhoosh: Sync on Workout Finish"
trigger:
  - platform: numeric_state
    entity_id: sensor.smart_trainer_power
    below: 15
    for:
      minutes: 2
action:
  - service: rest_command.trigger_mywhoosh_sync
```

### 4. Manual Verification via `curl`
```bash
# Background asynchronous trigger (recommended for Home Assistant)
curl -X POST http://<mywhoosh2garmin-host-ip>:8080/sync \
  -H "X-Webhook-Token: your_secure_webhook_token_here"

# Synchronous execution waiting for result
curl -X POST "http://<mywhoosh2garmin-host-ip>:8080/sync?wait=true" \
  -H "X-Webhook-Token: your_secure_webhook_token_here"
```

---

## 💻 Local Installation (Without Docker)

If you prefer to run the script directly on your host machine:

### 1. Requirements

* Python 3.10+
* pip

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Commands

```bash
# Check installed version
python -m src.main --version

# Sync only the single latest activity
python -m src.main --sync-latest

# Batch sync the last 10 activities
python -m src.main --batch 10

# Test run without uploading (simulation)
python -m src.main --dry-run

# Run as background daemon
python -m src.main --daemon --interval 60

# Show sync history database
python -m src.main --status
```

---

## 🧪 Running Tests

Unit tests are included and can be executed via:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This is an unofficial community project and is not affiliated with, maintained, or endorsed by MyWhoosh or Garmin. Use at your own discretion.
