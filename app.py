import gspread
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from oauth2client.service_account import ServiceAccountCredentials

# ১. পেজ কনফিগারেশন (সবার উপরে থাকতে হবে)
st.set_page_config(
    page_title="Banking & Insurance LMS", page_icon="🏛️", layout="wide"
)
# ২. PWA এবং কাস্টম CSS ডিজাইন ও হেডার ব্যানার

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
    /* সব বাটন এবং ফর্ম সাবমিট বাটনের ওপর কারসার নিলে নীল রঙ হবে */
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

  sheet = client.open("library_data").sheet1
  data = sheet.get_all_records()
  df = pd.DataFrame(data)
  df.columns = df.columns.str.strip()
  return df


try:
  catalog = load_data()
except Exception as e:
  st.error(
      f"Database connection error! Please check your Secrets configuration."
      f" Details: {e}"
  )
  catalog = pd.DataFrame()

# Session State for Local Data Storage (Issue requests, Book requests, Reviews)
if "issue_requests" not in st.session_state:
  st.session_state.issue_requests = []
if "book_requisitions" not in st.session_state:
  st.session_state.book_requisitions = []
if "book_reviews" not in st.session_state:
  st.session_state.book_reviews = []

# ৪. সাইডবার নেভিগেশন (নতুন অপশনগুলোসহ)
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    [
        "🔍 Book Search",
        "📖 Book Issue Request",
        "📝 New Book Request",
        "📌 Notice Board & Hours",
        "⭐ Book Reviews & Ratings",
        "🔒 Admin Portal",
    ],
)

# ৫. বই অনুসন্ধান (Live Search & Autocomplete)
if menu == "🔍 Book Search":
  st.subheader("📚 Library Book and Shelf Location Search")

  if not catalog.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric(label="📚 Total Book Titles", value=len(catalog))
    with col2:
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

    search_options = [
        f"{row['Title']} | Author: {row['Author']} | Subject: {row['Subject']} (Shelf: {row['Shelf_No']})"
        for _, row in catalog.iterrows()
    ]

    selected_option = st.selectbox(
        "Search by book title, author, subject, or shelf number:",
        options=search_options,
        index=None,
        placeholder=(
            "Start typing book title, author, subject, or shelf..."
        ),
    )

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

# ৬. বই ইস্যু রিকোয়েস্ট (Feature 1)
elif menu == "📖 Book Issue Request":
  st.subheader("📖 Book Issue / Borrow Request System")
  st.write(
      "Fill out the form below to request a book borrow ticket from the"
      " library."
  )

  with st.form("issue_form"):
    student_name = st.text_input("Full Name")
    student_id = st.text_input("Student ID / Roll")
    book_title = (
        st.selectbox("Select Book Title", catalog["Title"].tolist())
        if not catalog.empty
        else st.text_input("Book Title")
    )
    issue_days = st.slider(
        "Requested Duration (Days)", min_value=1, max_value=14, value=7
    )
    submit_issue = st.form_submit_button("Submit Borrow Request")

    if submit_issue:
      if student_name and student_id:
        st.session_state.issue_requests.append({
            "Name": student_name,
            "ID": student_id,
            "Book": book_title,
            "Duration": f"{issue_days} Days",
            "Status": "Pending Approval",
        })
        st.success(
            "✅ Your borrow request has been successfully submitted to the"
            " library admin!"
        )
      else:
        st.warning("⚠️ Please fill in all required fields.")

  if st.session_state.issue_requests:
    st.markdown("### 📋 Active Borrow Requests (Session)")
    st.dataframe(
        pd.DataFrame(st.session_state.issue_requests), use_container_width=True
    )

# ৭. নতুন বইয়ের রিকোয়েস্ট (Feature 3)
elif menu == "📝 New Book Request":
  st.subheader("📝 New Book Purchase Requisition Form")
  st.write(
      "Can't find a book in the library? Request the department to purchase"
      " it."
  )

  with st.form("req_form"):
    req_name = st.text_input("Your Name (Student/Faculty)")
    req_book = st.text_input("Suggested Book Title")
    req_author = st.text_input("Author Name")
    req_reason = st.text_area(
        "Why is this book necessary for the course/department?"
    )
    submit_req = st.form_submit_button("Send Book Request")

    if submit_req:
      if req_name and req_book:
        st.session_state.book_requisitions.append({
            "Requester": req_name,
            "Book": req_book,
            "Author": req_author,
            "Reason": req_reason,
            "Status": "Under Review",
        })
        st.success(
            "✅ Book purchase request submitted successfully! The library"
            " committee will review it."
        )
      else:
        st.warning("⚠️ Please enter your name and book title.")

  if st.session_state.book_requisitions:
    st.markdown("### 📋 Submitted Requisitions")
    st.dataframe(
        pd.DataFrame(st.session_state.book_requisitions),
        use_container_width=True,
    )

# ৮. নোটিশ বোর্ড ও সময়সূচী (Feature 4)
elif menu == "📌 Notice Board & Hours":
  st.subheader("📌 Digital Notice Board & Library Hours")

  col1, col2 = st.columns(2)

  with col1:
    with st.container(border=True):
      st.markdown("### ⏰ Library Schedule & Hours")
      st.markdown(
          """
            - **Sunday - Thursday:** 9:00 AM – 4:00 PM  
            - **Friday - Saturday:** Closed (Weekend)  
            - **Break Time:** 1:00 PM – 2:00 PM  
            - **Location:** Room No. 304, Department of Banking & Insurance, CU  
            """
      )

  with col2:
    with st.container(border=True):
      st.markdown("### 📢 Important Announcements")
      st.markdown(
          """
            - **New Arrivals:** 25+ new books on Financial Econometrics and Risk Management have been added to Shelf #4.  
            - **Return Policy:** Books must be returned within 7 days of issue to avoid late fines.  
            - **Quiet Zone:** Maintain strict silence inside the reading room.  
            """
      )

# ৯. বই রিভিউ ও রেটিং (Feature 5)
elif menu == "⭐ Book Reviews & Ratings":
  st.subheader("⭐ Book Ratings & Student Reviews")

  with st.form("review_form"):
    rev_book = (
        st.selectbox("Select Book to Review", catalog["Title"].tolist())
        if not catalog.empty
        else st.text_input("Book Title")
    )
    rev_user = st.text_input("Your Name")
    rating = st.slider("Rating (Stars)", 1, 5, 5)
    review_text = st.text_area("Write your feedback or review")
    submit_review = st.form_submit_button("Post Review")

    if submit_review:
      if rev_user and review_text:
        st.session_state.book_reviews.append({
            "Book": rev_book,
            "Reviewer": rev_user,
            "Rating": f"{'⭐' * rating} ({rating}/5)",
            "Review": review_text,
        })
        st.success("✅ Thank you for your valuable review!")
      else:
        st.warning("⚠️ Please enter your name and review text.")

  if st.session_state.book_reviews:
    st.markdown("### 📚 Recent Book Reviews")
    for r in st.session_state.book_reviews:
      with st.container(border=True):
        st.markdown(f"**📘 Book:** {r['Book']} | **Rating:** {r['Rating']}")
        st.markdown(f"*{r['Review']}* — **{r['Reviewer']}**")

# ১০. অ্যাডমিন পোর্টাল (পাসওয়ার্ড সুরক্ষিত)
elif menu == "🔒 Admin Portal":
  st.subheader("🔐 Administrator Login")
  admin_pass = st.text_input("Enter Admin Password", type="password")

  if admin_pass == "admin123":
    st.success("✅ Logged in successfully as Administrator!")
    st.markdown("### ⚙️ Library Management Dashboard")

    tab1, tab2, tab3 = st.tabs(
        ["📚 Catalog Management", "📖 Borrow Requests", "📝 Book Requisitions"]
    )

    with tab1:
      st.markdown("### Complete Book Catalog from Google Sheets")
      if not catalog.empty:
        st.dataframe(catalog, use_container_width=True)
      else:
        st.info("No data found.")

    with tab2:
      st.markdown("### Student Borrow Requests")
      if st.session_state.issue_requests:
        st.dataframe(
            pd.DataFrame(st.session_state.issue_requests),
            use_container_width=True,
        )
      else:
        st.info("No borrow requests pending.")

    with tab3:
      st.markdown("### Book Purchase Requisitions")
      if st.session_state.book_requisitions:
        st.dataframe(
            pd.DataFrame(st.session_state.book_requisitions),
            use_container_width=True,
        )
      else:
        st.info("No purchase requisitions found.")

  elif admin_pass:
    st.error("❌ Incorrect Password!")
  else:
    st.warning("⚠️ Please enter the password to access admin controls.")
