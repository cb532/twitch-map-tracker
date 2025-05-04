
# Twitch Map Detection & Tracking (Capstone Project)

Welcome to the official repository for my senior capstone project: a real-time Twitch map detection and dashboard system for Marvel Rivals livestreams.

This project uses OCR and keyword-based scoring to automatically detect and label **Marvel Rivals maps** from Twitch streams, storing results in a MySQL database and visualizing them on a live Streamlit dashboard.

---

## Features

- Real-time Marvel Rivals map detection from Twitch livestreams using OCR
- 99.13% validation accuracy on 1498 labeled screenshots
- Automatic screenshot capture on multiple streams constantly
- High-value keyword scoring system to enhance prediction accuracy
- Live-updating Streamlit dashboard with map and streamer filters
- MySQL database backend with persistent storage
- Deployed on Google Cloud VM for 24/7 operation

---

## Project Structure

```
├── main.py               # Main pipeline for detection, OCR, and DB insertion
├── app.py                # Streamlit dashboard frontend
├── /tmp/                 # Temporary storage for screenshots
├── requirements.txt      # Python dependencies
└── README.md             # Project overview (you are here)
```

---

## Getting Started

### 1. Prerequisites
- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- `ffmpeg` and `streamlink` installed system-wide
- Twitch API Client ID + OAuth Token
- MySQL database (schema below)
- `streamlit-autorefresh` for automatic dashboard updates
- Google Fonts (optional, for some matplotlib displays)

### 2. Clone the Repo
```bash
git clone https://github.com/yourusername/twitch-map-tracker.git
cd twitch-map-tracker
```

### 3. Set Environment Variables
```bash
export TWITCH_CLIENT_ID="your_client_id"
export TWITCH_OAUTH_TOKEN="your_oauth_token"
export MYSQL_HOST="localhost"
export MYSQL_USER="root"
export MYSQL_PASSWORD="your_password"
export MYSQL_DATABASE="twitch_data"
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## How It Works

### main.py
1. Checks if each configured Twitch streamer is live and playing *Marvel Rivals*
2. Captures a screenshot using `streamlink` piped into `ffmpeg`
3. Crops the top-left UI section using proportional dimensions
4. Runs OCR (via `pytesseract`) on the cropped section
5. Matches recognized words against mission texts using keyword scoring
6. Saves the best map prediction and image path to MySQL

### app.py
- Streamlit app that:
  - Connects to MySQL and fetches all recent detections
  - Displays:
    - Most recent map, streamer, and screenshot
    - Bar charts of top maps and top streamers
    - Full history table with filters
  - Auto-refreshes every 10 seconds

---

## Validation Results

| Mode                        | Correct | Incorrect | Accuracy  |
|-----------------------------|---------|-----------|-----------|
| Final Model                 | 1485    | 13        | 99.13%    |
| Without high-value keywords | 1463    | 35        | 97.66%    |
| Fuzzy matching only         | 1117    | 381       | 74.57%    |

Validation was performed on 1498 screenshots. The final model uses:
- Minimum 3 words recognized
- 60% OCR confidence threshold
- Keyword scoring system with high-value and super high-value words

---

## Database Schema (MySQL)
```sql
CREATE TABLE twitch_maps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    streamer VARCHAR(255),
    timestamp DATETIME,
    map VARCHAR(255),
    storage_path TEXT
);
```

---

## Potential Applications

The same pipeline can be extended to:
- Medical monitor screen parsing (e.g., vitals, device readouts)
- Retail shelf cam analysis (e.g., "out of stock" signs)
- Dashcam/license plate OCR and incident flagging
- Esports overlays and match tracking
- Stream-based data gathering for machine learning

---

## Tech Stack
- Python
- OpenCV / pytesseract
- Streamlink + ffmpeg
- MySQL
- Streamlit
- Google Cloud VM (Ubuntu)

---
