import streamlit as st
import serial
import time
import os

# --- Page Config ---
st.set_page_config(page_title="Robotic Arm Control", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Main app background gradient */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 50%, #f4e2d8 100%);
    }
    
    /* Title styling */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: -15px;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 400;
        color: #475569;
        margin-bottom: 30px;
    }
    
    /* Status Text Styling */
    .status-online {
        color: #16a34a;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
        background-color: #dcfce7;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #16a34a;
    }
    .status-offline {
        color: #dc2626;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
        background-color: #fee2e2;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dc2626;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session states
if 'ser' not in st.session_state:
    st.session_state.ser = None
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False

# --- Serial Connection Sidebar ---
st.sidebar.header("🔌 Connection Settings")
port = st.sidebar.text_input("Serial Port", value="COM3") 
baud = st.sidebar.selectbox("Baud Rate", [9600, 115200], index=0)

def connect_serial():
    try:
        # Close existing connection if one is stuck open
        if st.session_state.ser and st.session_state.ser.is_open:
            st.session_state.ser.close()
            
        st.session_state.ser = serial.Serial(port, baud, timeout=1)
        st.session_state.is_connected = True
        st.sidebar.success(f"Connected to {port}!")
        st.toast("Waiting for Arduino to initialize...")
        time.sleep(2) # CRITICAL: Gives Arduino time to boot after serial reset
    except Exception as e:
        st.session_state.is_connected = False
        st.session_state.ser = None
        st.sidebar.error(f"Connection Failed: Ensure {port} is correct and not busy.")

if st.sidebar.button("Connect to Hardware", type="primary", use_container_width=True):
    connect_serial()

def send_command(channel, angle):
    cmd = f"{channel}:{angle}\n"
    # STRICT HARDWARE CHECK
    if st.session_state.is_connected and st.session_state.ser and st.session_state.ser.is_open:
        try:
            st.session_state.ser.write(cmd.encode())
            st.toast(f"Sent: {cmd.strip()}")
        except Exception as e:
            st.error(f"Failed to send data: {e}")
            st.session_state.is_connected = False
    else:
        st.error("⚠️ Hardware not connected! Please connect via the sidebar first.")

# --- Main Layout ---
st.markdown('<div class="main-header">Internet of Things Project</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">🤖 Robotic Arm Dashboard</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([4, 6], gap="large")

with col_left:
    st.subheader("Hardware Status")
    
    # Image Rendering
    image_path = "hardware.png"
    if os.path.exists(image_path):
        st.image(image_path, use_column_width=True, caption="Robotic Arm Prototype")
    else:
        st.info("📷 Place 'hardware.png' in this folder to display your machine here.")
    
    # Status Indicator
    if st.session_state.is_connected:
        st.markdown('<div class="status-online">🟢 STATUS: ONLINE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">🔴 STATUS: OFFLINE</div>', unsafe_allow_html=True)

with col_right:
    st.subheader("Manual Joint Control")
    
    controls = [
        ("Base Rotation", 0, 0, 180, 90),
        ("Shoulder", 2, 0, 180, 90),
        ("Joint 2", 3, 0, 180, 90),
        ("Joint 3", 4, 0, 180, 90),
        ("Gripper Pitch", 5, 0, 180, 90),
        ("Gripper Open/Close", 6, 0, 180, 90),
    ]

    for label, ch, min_v, max_v, default in controls:
        val = st.slider(f"{label} (Ch {ch})", min_v, max_v, default, key=f"slider_{ch}")
        if st.button(f"Send {label} Command", key=f"btn_{ch}", use_container_width=True):
            send_command(ch, val)

    st.divider()

    if st.button("Center All Joints (Reset)", type="primary", use_container_width=True):
        for _, ch, _, _, _ in controls:
            send_command(ch, 90)
            time.sleep(0.1) # Prevents overwhelming the serial buffer