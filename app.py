import streamlit as st
import pymysql
import pandas as pd
import time
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# Streamlit Page Configuration
st.set_page_config(
    page_title="Twitch Map Tracking Dashboard",
    page_icon="🎮",
    layout="wide"
)

# Auto-refresh every 10 seconds
st_autorefresh(interval=10 * 1000, limit=None, key="autorefresh")

st.markdown("## 🎮 Twitch Map Tracking Dashboard")
st.write("Live tracking of maps detected from Twitch streams.")

# Database Configuration
# load DB credentials from environment
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST"),
    "user":     os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "database": os.environ.get("MYSQL_DATABASE"),
}

# Database Connection Function
def connect_to_db(retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            connection = pymysql.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
            )
            return connection
        except pymysql.MySQLError as e:
            st.error(f"Database connection failed (Attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
    st.error("All connection attempts failed. Check database status and credentials.")
    return None

# Fetch data from the database
def fetch_data():
    connection = connect_to_db()
    if not connection:
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM twitch_maps ORDER BY timestamp DESC")
            data = cursor.fetchall()

        return pd.DataFrame(data) if data else None

    except pymysql.MySQLError as e:
        st.error(f"Database query failed: {e}")
        return None

    finally:
        connection.close()

# Main App
# Load and filter data
df = fetch_data()

if df is not None and not df.empty:
    # Sidebar filters
    st.sidebar.header("Filter Options")
    streamer_options = ["All"] + sorted(df["streamer"].unique())
    map_options = ["All"] + sorted(df["map"].unique())

    selected_streamer = st.sidebar.selectbox("Streamer", streamer_options)
    selected_map = st.sidebar.selectbox("Map", map_options)

    if selected_streamer != "All":
        df = df[df["streamer"] == selected_streamer]
    if selected_map != "All":
        df = df[df["map"] == selected_map]

    # Metric summary
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🧠 Total Detections", len(df))
    col_b.metric("🗺️ Unique Maps", df["map"].nunique())
    col_c.metric("📺 Unique Streamers", df["streamer"].nunique())

    # Tabbed layout for content
    tab1, tab2, tab3 = st.tabs(["📍 Latest Detection", "📊 Stats", "📅 Table"])

    with tab1:
        non_unknown_df = df[df["map"] != "Unknown Map"]
        if not non_unknown_df.empty:
            latest_row = non_unknown_df.iloc[0]

            # Convert timestamp to EST
            utc_time = pd.to_datetime(latest_row['timestamp']).tz_localize('UTC')
            est_time = utc_time.tz_convert('US/Eastern')
            formatted_time = est_time.strftime('%b %d, %-I:%M %p EST')

            st.markdown(f"**{latest_row['streamer']} on {latest_row['map']} at {formatted_time}**")
            st.image(latest_row["storage_path"], use_container_width=True)
        else:
            st.markdown("_No non-unknown map detections available yet._")
            st.image(latest_row["storage_path"], use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top 5 Streamers")
            top_streamers = df["streamer"].value_counts().head(5)
            fig, ax = plt.subplots()
            top_streamers.plot(kind="bar", ax=ax)
            ax.set_ylabel("Detections")
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            plt.tight_layout()
            st.pyplot(fig)

        with col2:
            st.markdown("#### Most Detected Maps")
            top_maps = df[df["map"] != "Unknown Map"]["map"].value_counts().sort_values(ascending=True)
            fig, ax = plt.subplots()
            top_maps.plot(kind="barh", color="orange", ax=ax)
            ax.set_ylabel("Frequency")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')
            plt.tight_layout()
            st.pyplot(fig)

    with tab3:
        st.dataframe(df.reset_index(drop=True))    

else:
    st.warning(" No data available yet. Please wait for new data.")