import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# ১. পেজ কনফিগারেশন (সবার উপরে থাকতে হবে)
st.set_page_config(
    page_title="Departmental Library | CU", page_icon="🏛️", layout="wide"
)

# ২. কাস্টম CSS ডিজাইন ও হেডার ব্যানার
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
    </style>
    
    <div class="header-box">
        <h1>🏛️ Departmental Library Management System</h1>
        <p>Department of Banking & Insurance • University of Chittagong</p>
    </div>
""",
    unsafe_allow_html=True,
)


# ৩. গুগল শিট কানেকশন ফাংশন
@st.cache_resource
def load_data():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  client = gspread.authorize(creds)

# ৩. গুগল শিট কানেকশন ফাংশন
@st.cache_resource
def load_data():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  client = gspread.authorize(creds)

  # আপনার গুগল শিটের নাম এখানে থাকবে
  sheet = client.open("library_data").sheet1
  data = sheet.get_all_records()
  df = pd.DataFrame(data)

  # কলামের নামের চারপাশের যেকোনো লুকানো স্পেস পরিষ্কার করার জন্য
  df.columns = df.columns.str.strip()
  return df

# ৪. সাইডবার মেনু
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to", ["🔍 বই অনুসন্ধান", "🔒 Admin Portal (Faculty/Staff)"]
)

# ৫. বই অনুসন্ধান (সবার জন্য উন্মুক্ত ও লাইভ সাজেশনসহ)
if menu == "🔍 বই অনুসন্ধান":
  st.subheader("📚 Library Book and Shelf Location Search")

  if not catalog.empty:
    # ড্যাশবোর্ড স্ট্যাটাস কার্ড (KPI Metrics)
    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric(label="📚 Total Book Titles", value=len(catalog))
    with col2:
      # নিরাপদভাবে সংখ্যা হিসাব করার জন্য pd.to_numeric ব্যবহার করা হলো
      if "Available_Copies" in catalog.columns:
        total_copies = int(
            pd.to_numeric(catalog["Available_Copies"], errors="coerce")
            .fillna(0)
            .sum()
        )
      else:
        total_copies = len(catalog)
      st.metric(label="📖 Available Copies", value=total_copies)
    with col3:
      total_subjects = (
          catalog["Subject"].nunique() if "Subject" in catalog.columns else "N/A"
      )
      st.metric(label="🗂️ Total Subjects", value=total_subjects)
        
    st.markdown("---")

    # প্রতিটি বইয়ের জন্য সার্চযোগ্য অপشن তৈরি
    search_options = [
        f"{row['Title']} | Author: {row['Author']} | Subject: {row['Subject']} (Shelf: {row['Shelf_No']})"
        for _, row in catalog.iterrows()
    ]

    # টাইপ করার সাথে সাথে সাজেশন দেখানোর জন্য selectbox
    selected_option = st.selectbox(
        "Search by book title, author, subject, or shelf number:",
        options=search_options,
        index=None,
        placeholder=(
            "Start typing book title, author, subject, or shelf..."
        ),
    )

    # সিলেক্ট করলে সুন্দর কার্ডে ডিটেইলস দেখাবে
    if selected_option:
      selected_title = selected_option.split(" | Author:")[0]
      book = catalog[catalog["Title"] == selected_title].iloc[0]

      with st.container(border=True):
        st.markdown(f"### 📘 {book['Title']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**✍️ Author:**  \n{book['Author']}")
        c2.markdown(f"**🏷️ Subject:**  \n{book['Subject']}")
        c3.markdown(f"**📍 Shelf No:**  \n`{book['Shelf_No']}`")
        c4.markdown(f"**📦 Available:**  \n{book['Available_Copies']} Copies")

      st.markdown("### 📋 Filtered Record")
      st.dataframe(
          catalog[catalog["Title"] == selected_title],
          use_container_width=True,
      )
    else:
      st.markdown("### 📖 Complete Book Catalog")
      st.dataframe(catalog, use_container_width=True)
  else:
    st.info("No books available in the catalog.")

# ৬. অ্যাডমিন পোর্টাল (পাসওয়ার্ড সুরক্ষিত)
elif menu == "🔒 Admin Portal (Faculty/Staff)":
  st.subheader("🔐 Administrator Login")
  admin_pass = st.text_input("Enter Admin Password", type="password")

  # আপনার পছন্দমতো পাসওয়ার্ড এখানে দিতে পারেন (যেমন: admin123)
  if admin_pass == "admin123":
    st.success("✅ Logged in successfully as Administrator!")
    st.markdown("### ⚙️ Library Management Dashboard")
    st.write(
        "Here you can add, update, or manage book records connected with"
        " Google Sheets."
    )

    # অ্যাডমিন প্যানেলে ফুল ডাটা টেবিল এডিটিংয়ের সুবিধা
    if not catalog.empty:
      st.dataframe(catalog, use_container_width=True)
    else:
      st.info("No data found to manage.")
  elif admin_pass:
    st.error("❌ Incorrect Password! Please try again.")
  else:
    st.warning("⚠️ Please enter the password to access admin controls.")
