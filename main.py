# import standard and external libraries
import os
import time
import subprocess
import requests
import json
import cv2
import pytesseract
import mysql.connector
import re
from fuzzywuzzy import process

# ------------------ ENV / CONFIG ------------------ #
# Twitch API credentials
# get Twitch API credentials from environment
CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
OAUTH_TOKEN = os.environ.get("TWITCH_OAUTH_TOKEN")

# Streamers you want to monitor (comma separated in an env var, or define here as a list)
# list of streamers to monitor
STREAMERS = ["dongm1n_", "doomed_ow", "calwya", "GURU", "Gale", "storytimebed", "space", "m4rchgg", "eatinpizzarn", "shroud", "Impuniti", "senorhoff", "Kephrii", "ange1inac", "farpwr", "MaleniaMR", "FullMetalLamp"]

# Database connection info  
# database connection settings from environment
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST"),
    "user":     os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "database": os.environ.get("MYSQL_DATABASE"),
}

# Capture interval in seconds
# how often to check for streamers (in seconds)
CHECK_INTERVAL = 5

# OCR / Fuzzy Matching
CONFIDENCE_THRESHOLD = 60
MIN_WORDS_REQUIRED = 3

# keywords used to boost map confidence
SUPER_HIGH_VALUE_WORDS = {
    "draculas", "ratatoskr", "castle", "ritual", "final", "montesi", "vampires", "darkhold",
    "herbie", "tower", "chronovium", "vibrani", "by", "off", "prison", "field", "force",
    "knull", "kn", "explosion", "scan", "pages", "scanning", "repair", "master", "weaver",
    "des", "save", "lokis", "destro", "garden", "bifrost", "archive", "odins", "room",
    "throne", "eldritch", "monument", "station", "frozen", "airfield", "monitoring", "factory",
    "laboratory", "soldier", "super", "chrono", "experiment", "area", "vibranium", "ground",
    "imperial", "dueling", "spaceport", "stellar", "cerebro", "taking", "cradle", "ultrons",
    "invasion", "carousel", "infecting", "grove", "budokan", "jarnbjorn", "yggdrasill",
    "device", "tapping", "strive", "team"
}

HIGH_VALUE_WORDS = {
    "use", "eliminate", "formula", "sealed", "return", "place", "bast", "meditation",
    "its", "chamber", "statue", "returning", "islands", "destroy", "essence", "underground",
    "avengers", "lost", "life", "destiny", "web", "jarnbjorn", "yggdrasill", "tapping",
    "device", "ultron", "krakoa", "rescue", "rescued", "being", "tower", "zero", "spider"
}

# Dictionary mapping objectives to maps
# text-to-map matching dictionary
MAP_OBJECTIVES = {
    "Enter Draculas Castle and stop his final ritual Rescue the sealed Ratatoskr": "Central Park Attack",
    "Enter Draculas Castle and stop his final ritual Stop Draculas final ritual": "Central Park Attack",
    "Use the Montesi Formula to eliminate all the vampires Prevent Ratatoskr from being rescued": "Central Park Defence",
    "Use the Montesi Formula to eliminate all the vampires Get the Montesi Formula off Ratatoskr": "Central Park Defence",

    "Help the Statue of Bast Return to Its Place Rescue the Statue of Bast Sealed by the Vibrani Chronovium": "Hall of Djalia Attack",
    "Help the Statue of Bast Return to Its Place Escort the Statue to the Meditation Chamber": "Hall of Djalia Attack",
    "Prevent the Statue of Bast From Returning to Its Place Prevent the Statue of Bast From Being Rescued": "Hall of Djalia Defence",
    "Prevent the Statue of Bast From Returning to Its Place Prevent the Statue From Reaching the Meditation Chamber": "Hall of Djalia Defence",

    "Help Spider Zero Return to the Spider Islands Rescue Spider Zero from the Force Field Prison": "Shinshibuya Attack",
    "Help Spider Zero Return to the Spider Islands Escort Spider Zero to Budokan": "Shinshibuya Attack",
    "Stop Spider Zero from Returning to the Spider Islands Stop Spider Zero from Being Rescued": "Shinshibuya Defence",
    "Stop Spider Zero from Returning to the Spider Islands Stop Spider Zero from reaching Budokan": "Shinshibuya Defence",

    "Escort Knulls Essence to the Underground Prepare to Capture Knulls Essence": "Symbiotic Surface Attack",
    "Escort Knulls Essence to the Underground Go Underground and Destroy Knull with Knulls Essence": "Symbiotic Surface Attack",
    "Stop Knulls Essence from Going Underground Stop the Explosion of Knulls Essence to Prevent Kn": "Symbiotic Surface Defence",
    "Stop Knulls Essence from Going Underground Defend Knulls Essence": "Symbiotic Surface Defence",

    "Help HERBIE scan all the lost pages of the Darkhold Escort HERBIE to Avengers Tower": "Midtown Attack",
    "Prevent HERBIE from scanning all the lost Prevent HERBIE from reaching the Avengers Tower": "Midtown Defence",

    "Help Spider Zero Repair the Web of Life and Destiny Escort Spider Zero to the Web of Life and Destiny": "Spider Islands Attack",
    "Help the Master Weaver Save the Web of Life and Des Stop Spider Zero from reaching the Web of Life and Destiny": "Spider Islands Defence",

    "Destroy Lokis Yggdrasill Tapping Device Escort Jarnbjorn to Yggdrasill": "Yggdrasill Path Attack",
    "Stop the Yggdrasill Tapping Device from Being Destro Prevent Jarnbjorn from Reaching Yggdrasill": "Yggdrasill Path Defence",

    "Capture the Bifrost Garden Prepare to Head to the Bifrost Garden": "Royale Palace Bifrost Garden",
    "Capture the Bifrost Garden Prepare to Capture the Bifrost Garden": "Royale Palace Bifrost Garden",
    "Capture the Bifrost Garden Defend the Bifrost Garden": "Royale Palace Bifrost Garden",
    "Capture the Bifrost Garden Reclaim the Bifrost Garden": "Royale Palace Bifrost Garden",
    "Capture Odins Archive Prepare to Head to Odins Archive": "Royale Palace Odins Archive",
    "Capture Odins Archive Prepare to Capture Odins Archive": "Royale Palace Odins Archive",
    "Capture Odins Archive Defend Odins Archive": "Royale Palace Odins Archive",
    "Capture Odins Archive Reclaim Odins Archive": "Royale Palace Odins Archive",
    "Capture the Throne Room Prepare to Head to the Throne Room": "Royale Palace Throne Room",
    "Capture the Throne Room Prepare to Capture the Throne Room": "Royale Palace Throne Room",
    "Capture the Throne Room Defend the Throne Room": "Royale Palace Throne Room",
    "Capture the Throne Room Reclaim the Throne Room": "Royale Palace Throne Room",

    "Capture Eldritch Monument Prepare to Head to Eldritch Monument": "Hells Heaven Eldritch Monument",
    "Capture Eldritch Monument Prepare to Capture Eldritch Monument": "Hells Heaven Eldritch Monument",
    "Capture Eldritch Monument Defend Eldritch Monument": "Hells Heaven Eldritch Monument",
    "Capture Eldritch Monument Reclaim Eldritch Monument": "Hells Heaven Eldritch Monument",
    "Capture Frozen Airfield Prepare to Head to Frozen Monitoring Station": "Hells Heaven Frozen Airfield",
    "Capture Frozen Airfield Prepare to Capture Frozen Monitoring Station": "Hells Heaven Frozen Airfield",
    "Capture Frozen Airfield Defend Frozen Monitoring Station": "Hells Heaven Frozen Airfield",
    "Capture Frozen Airfield Reclaim Frozen Monitoring Station": "Hells Heaven Frozen Airfield",
    "Capture Super Soldier Factory Prepare to Head to Super Soldier Laboratory": "Hells Heaven Super Soldier Factory",
    "Capture Super Soldier Factory Prepare to Capture Super Soldier Laboratory": "Hells Heaven Super Soldier Factory",
    "Capture Super Soldier Factory Defend Super Soldier Laboratory": "Hells Heaven Super Soldier Factory",
    "Capture Super Soldier Factory Reclaim Super Soldier Laboratory": "Hells Heaven Super Soldier Factory",

    "Capture the Chrono Vibranium Experiment Area Prepare to Head to the Chrono Vibranium Experiment Area": "Brinin Tchalla Experiment Area",
    "Capture the Chrono Vibranium Experiment Area Prepare to Capture the Chrono Vibranium Experiment Area": "Brinin Tchalla Experiment Area",
    "Capture the Chrono Vibranium Experiment Area Defend the Chrono Vibranium Experiment Area": "Brinin Tchalla Experiment Area",
    "Capture the Chrono Vibranium Experiment Area Reclaim the Chrono Vibranium Experiment Area": "Brinin Tchalla Experiment Area",
    "Capture the Imperial Dueling Ground Prepare to Head to the Imperial Dueling Ground": "Brinin Tchalla Imperial Dueling Ground",
    "Capture the Imperial Dueling Ground Prepare to Capture the Imperial Dueling Ground": "Brinin Tchalla Imperial Dueling Ground",
    "Capture the Imperial Dueling Ground Defend the Imperial Dueling Ground": "Brinin Tchalla Imperial Dueling Ground",
    "Capture the Imperial Dueling Ground Reclaim the Imperial Dueling Ground": "Brinin Tchalla Imperial Dueling Ground",
    "Capture the Stellar Spaceport Prepare to Head to the Stellar Spaceport": "Brinin Tchalla Stellar Spaceport",
    "Capture the Stellar Spaceport Prepare to Capture the Stellar Spaceport": "Brinin Tchalla Stellar Spaceport",
    "Capture the Stellar Spaceport Defend the Stellar Spaceport": "Brinin Tchalla Stellar Spaceport",
    "Capture the Stellar Spaceport Reclaim the Stellar Spaceport": "Brinin Tchalla Stellar Spaceport",

    "Capture the Cradle Stop Ultron From Taking Cerebro Prepare to Head to the Cradle": "Krokoa Cradle",
    "Capture the Cradle Stop Ultron From Taking Cerebro Prepare to Capture the Cradle": "Krokoa Cradle",
    "Capture the Cradle Stop Ultron From Taking Cerebro Defend the Cradle": "Krokoa Cradle",
    "Capture the Cradle Stop Ultron From Taking Cerebro Reclaim the Cradle": "Krokoa Cradle",
    "Capture the Carousel Stop Ultrons Invasion of Krakoa Prepare to Head to the Carousel": "Krokoa Carousel",
    "Capture the Carousel Stop Ultrons Invasion of Krakoa Prepare to Capture the Carousel": "Krokoa Carousel",
    "Capture the Carousel Stop Ultrons Invasion of Krakoa Defend the Carousel": "Krokoa Carousel",
    "Capture the Carousel Stop Ultrons Invasion of Krakoa Reclaim the Carousel": "Krokoa Carousel",
    "Capture the Grove Stop Ultron From Infecting Krakoa Prepare to Head to The Grove": "Krokoa Grove",
    "Capture the Grove Stop Ultron From Infecting Krakoa Prepare to Capture The Grove": "Krokoa Grove",
    "Capture the Grove Stop Ultron From Infecting Krakoa Defend The Grove": "Krokoa Grove",
    "Capture the Grove Stop Ultron From Infecting Krakoa Reclaim The Grove": "Krokoa Grove",

    "Be the first team to reach 16 points Strive to eliminate more enemies": "Doom match",
}

# runs OCR on cropped image and returns confident words
def extract_top_left_text(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Unable to read image at {image_path}")
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Proportional cropping
    h, w = gray.shape
    top = int(h * 0.032)
    bottom = int(h * 0.093)
    left = int(w * 0.013)
    right = int(w * 0.313)
    cropped_region = gray[top:bottom, left:right]

    ocr_data = pytesseract.image_to_data(cropped_region, config="--psm 6", output_type=pytesseract.Output.DICT)
    extracted_phrases = []
    for i in range(len(ocr_data["text"])):
        text = ocr_data["text"][i].strip()
        try:
            conf = int(ocr_data["conf"][i])
        except ValueError:
            conf = 0
        if text and conf >= CONFIDENCE_THRESHOLD:
            extracted_phrases.append((text, conf))
    return extracted_phrases

# basic cleaning to normalize extracted text
def clean_text(text):
    text = text.lower()
    text = text.replace(".", "")
    text = text.replace("-", " ")
    text = text.replace("'", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

# scores and matches recognized words to map objectives
def detect_map(phrases):
    high_conf_words = [word for word, conf in phrases if conf >= 80]
    if len(high_conf_words) < MIN_WORDS_REQUIRED:
        return [("Unknown Map", 0)]
    extracted_text = " ".join([p[0] for p in phrases])
    cleaned_ocr = clean_text(extracted_text)
    recognized_words = set(cleaned_ocr.split())
    keyword_matches = []
# text-to-map matching dictionary
    for obj_text, map_name in MAP_OBJECTIVES.items():
        words_matched = 0
        super_high_value_count = 0
        high_value_count = 0
        for word in recognized_words:
            if word in obj_text.lower():
                words_matched += 1
# keywords used to boost map confidence
                if word in SUPER_HIGH_VALUE_WORDS:
                    super_high_value_count += 1
                elif word in HIGH_VALUE_WORDS:
                    high_value_count += 1
        if words_matched > 1:
            score = 50 + (words_matched * 5) + (high_value_count * 15) + (super_high_value_count * 30)
            keyword_matches.append((map_name, score))
    if keyword_matches:
        return sorted(keyword_matches, key=lambda x: x[1], reverse=True)
    return [("Unknown Map", 0)]

# saves result to MySQL database
def save_to_database(streamer, timestamp, detected_map, storage_path):
    try:
# database connection settings from environment
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """INSERT INTO twitch_maps (streamer, timestamp, map, storage_path) VALUES (%s, %s, %s, %s)"""
        cursor.execute(query, (streamer, timestamp, detected_map, storage_path))
        conn.commit()
        print(f"Inserted into DB: {streamer}, {timestamp}, {detected_map}, {storage_path}")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# checks if a streamer is live and playing Marvel Rivals
def check_online(streamer):
    url = "https://api.twitch.tv/helix/streams"
    headers = {
# get Twitch API credentials from environment
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {OAUTH_TOKEN}"
    }
    try:
        r = requests.get(url, headers=headers, params={"user_login": streamer})
        if r.status_code != 200:
            print(f"Twitch API request failed [{r.status_code}]: {r.text}")
            return False
        data = r.json().get("data", [])
        if not data:
            return False
        stream_info = data[0]
        game_name = stream_info.get("game_name", "").lower()
        if "marvel rivals" in game_name:
            print(f"{streamer} is playing Marvel Rivals.")
            return True
        else:
            print(f"{streamer} is live but playing '{stream_info.get('game_name', 'Unknown')}' instead of Marvel Rivals.")
            return False
    except requests.RequestException as e:
        print(f"Network error checking {streamer} live status: {e}")
        return False

# captures screenshot, processes OCR, and stores result
def capture_screenshot(streamer):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    safe_timestamp = timestamp.replace(" ", "_").replace(":", "-")
    output_file = f"/tmp/{streamer}_{safe_timestamp}.png"
    stream_url = f"https://www.twitch.tv/{streamer}"
    try:
        subprocess.run(
            f"streamlink --twitch-disable-ads {stream_url} best --stdout | ffmpeg -i pipe:0 -frames:v 1 {output_file}",
            shell=True,
            check=True
        )
        extracted_phrases = extract_top_left_text(output_file)
        print("Extracted Text & Confidence Scores:")
        if extracted_phrases:
            for text, conf in extracted_phrases:
                print(f" - '{text}' (Confidence: {conf}%)")
        else:
            print(" - No text found above confidence threshold.")
        maps_detected = detect_map(extracted_phrases)
        print("\nTop 3 Map Matches (Filtered & Weighted):")
        if not maps_detected or maps_detected[0][1] == 0:
            print("No maps detected with high confidence.")
            best_map = "Unknown Map"
        else:
            for i, (map_name, score) in enumerate(maps_detected[:3], 1):
                print(f"{i}. {map_name} ({score}%)")
            best_map = maps_detected[0][0]
        save_to_database(streamer, timestamp, best_map, output_file)
        print(f"Screenshot saved: {output_file} | Best map: {best_map}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error capturing screenshot from {streamer}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# main loop to check all streamers
def run_loop():
    while True:
        for streamer in STREAMERS:
            if check_online(streamer):
                print(f"{streamer} is LIVE! Capturing screenshot...")
                capture_screenshot(streamer)
            else:
                print(f"{streamer} is offline.")
        print(f"\nWaiting {CHECK_INTERVAL} seconds for next check...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_loop()