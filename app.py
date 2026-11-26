import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import streamlit as st

# ১. পেজ কনফিগারেশন (সবার উপরে থাকতে হবে)
st.set_page_config(
    page_title="Banking & Insurance LMS", page_icon="🏛️", layout="wide"
)

# ২. কাস্টম CSS ডিজাইন, বাটন হোভার ও হেডার ব্যানার
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .header-box {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .header-box h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
    }
    .header-box p {
        margin: 5px 0 0 0;
        font-size: 15px;
        color: #e0e8f5;
    }

    /* সব বাটন ও ফর্ম সাবমিট বাটনের ওপর কারসার নিলে নীল রঙ */
    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #1e3c72 !important;
        color: #ffffff !important;
        border-color: #1e3c72 !important;
        transition: all 0.2s ease-in-out;
    }
    </style>

    <div class="header-box">
        <h1>🏛️ Departmental Library Management System</h1>
        <p>Department of Banking & Insurance • University of Chittagong</p>
    </div>
""",
    unsafe_allow_html=True,
)


# ৩. গুগল শিট কানেকশন ফাংশন (কলাম স্পেস ক্লিনিং সহ)
@st.cache_resource
def load_data():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  client = gspread.authorize(creds)

  sheet = client.open("library_data").sheet1
  data = sheet.get_all_records()
  df = pd.DataFrame(data)
  df.columns = df.columns.str.strip()
  return df


# ৪. বইয়ের নাম ও লেখক থেকে নিজে থেকে নেট থেকে মলাট খোঁজার ফাংশন
@st.cache_data(show_spinner=False)
def fetch_book_cover(title, author=""):
  fallback_img = "https://img.icons8.com/color/240/open-book--v2.png"
  # আপনার GitHub রিপোজিটরিতে আপলোড করা জার্নালের মলাটের Raw লিংক নিচে বসান
  cu_journal_cover = "আপনার_কপি_করা_RAW_লিংকটি_এখানে_বসান"

  try:
    clean_title = str(title).strip() if pd.notna(title) else ""
    clean_author = str(author).strip() if pd.notna(author) else ""

    # জার্নালের নামের সাথে মিললে সব সময় নির্দিষ্ট মলাট দেখাবে
    if (
