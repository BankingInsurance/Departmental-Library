from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="ডিপার্টমেন্টাল লাইব্রেরি ম্যানেজমেন্ট", layout="wide"
)

# --- গুগল শিট কানেকশন সেটআপ ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
# Streamlit Secrets থেকে ক্রেডেনশিয়াল লোড করা হবে
creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# আপনার গুগল শিটের নাম এখানে দিতে হবে
SHEET_NAME = "Library_Database"
sheet = client.open(SHEET_NAME)


def load_data():
  catalog_sheet = sheet.worksheet("Catalog")
  issue_sheet = sheet.worksheet("Issue_Log")

  catalog_data = catalog_sheet.get_all_records()
  issue_data = issue_sheet.get_all_records()

  catalog = pd.DataFrame(catalog_data)
  issue_log = pd.DataFrame(issue_data)

  # যদি শিট খালি থাকে তবে ডিফল্ট কলাম নিশ্চিত করা
  if catalog.empty:
    catalog = pd.DataFrame(columns=[
        "Book_ID",
        "Title",
        "Author",
        "Subject",
        "Shelf_No",
        "Total_Copies",
        "Available_Copies",
    ])
  if issue_log.empty:
    issue_log = pd.DataFrame(columns=[
        "Issue_ID",
        "Book_ID",
        "Borrower_Name",
        "Role_ID",
        "Issue_Date",
        "Return_Deadline",
        "Status",
    ])

  return catalog, issue_log


def save_data(catalog_df, issue_df):
  catalog_sheet = sheet.worksheet("Catalog")
  issue_sheet = sheet.worksheet("Issue_Log")

  # ক্যাটালগ আপডেট
  catalog_sheet.clear()
  catalog_sheet.update(
      [catalog_df.columns.values.tolist()] + catalog_df.values.tolist()
  )

  # ইস্যু লগ আপডেট
  issue_sheet.clear()
  issue_sheet.update(
      [issue_df.columns.values.tolist()] + issue_df.values.tolist()
  )


# ডাটা লোড
catalog, issue_log = load_data()

st.title("📚 Banking & Insurance LMS")
st.markdown("---")

# --- সিকিউরিটি ও মেনু কন্ট্রোল ---
st.sidebar.header("🧭 মেনু ও কন্ট্রোল প্যানেল")
menu_options = ["🔍 বই অনুসন্ধান"]

st.sidebar.markdown("---")
st.sidebar.subheader("🔐 লাইব্রেরিয়ান লগইন (Admin)")
admin_checkbox = st.sidebar.checkbox("অ্যাডমিন মোড অন করুন")

if admin_checkbox:
  password = st.sidebar.text_input("অ্যাডমিন পাসওয়ার্ড দিন", type="password")
  if password == "1234":
    st.sidebar.success("লগইন সফল!")
    menu_options = [
        "🔍 বই অনুসন্ধান",
        "📥 নতুন বই এন্ট্রি",
        "📤 বই ইস্যু করুন",
        "🔄 বই জমা নিন",
        "📋 ইস্যু রেজিস্টার",
    ]
  elif password:
    st.sidebar.error("ভুল পাসওয়ার্ড!")

menu = st.sidebar.radio("সিলেক্ট করুন", menu_options)

# ১. বই অনুসন্ধান (সবার জন্য উন্মুক্ত)
if menu == "🔍 বই অনুসন্ধান":
  st.subheader("লাইব্রেরির বই ও সেলফ লোকেশন সার্চ")
  search_term = st.text_input(
      "বইয়ের নাম, লেখক, বিষয় বা সেলফ নম্বর দিয়ে সার্চ করুন:"
  )

  if search_term and not catalog.empty:
    filtered = catalog[
        catalog["Title"].astype(str).str.contains(search_term, case=False)
        | catalog["Author"].astype(str).str.contains(search_term, case=False)
        | catalog["Subject"].astype(str).str.contains(search_term, case=False)
        | catalog["Shelf_No"].astype(str).str.contains(search_term, case=False)
    ]
    st.dataframe(filtered, use_container_width=True)
  else:
    st.dataframe(catalog, use_container_width=True)

# ২. নতুন বই এন্ট্রি
elif menu == "📥 নতুন বই এন্ট্রি":
  st.subheader("ক্যাটালগে নতুন বই যুক্ত করুন")
  with st.form("add_book_form"):
    col1, col2 = st.columns(2)
    with col1:
      b_id = st.text_input("বুক আইডি (যেমন: B-101)")
      title = st.text_input("বইয়ের নাম")
      author = st.text_input("লেখক")
    with col2:
      subject = st.text_input("বিষয় (Subject)")
      shelf = st.text_input("সেলফ/র্যাক নম্বর (যেমন: Rack A-02)")
      copies = st.number_input("মোট সংখ্যা", min_value=1, value=1)

    submit = st.form_submit_button("বই সংরক্ষণ করুন")

    if submit:
      if not catalog.empty and b_id in catalog["Book_ID"].values:
        st.error("এই বুক আইডি ইতিমধ্যেই বিদ্যমান!")
      else:
        new_row = pd.DataFrame([{
            "Book_ID": b_id,
            "Title": title,
            "Author": author,
            "Subject": subject,
            "Shelf_No": shelf,
            "Total_Copies": copies,
            "Available_Copies": copies,
        }])
        catalog = pd.concat([catalog, new_row], ignore_index=True)
        save_data(catalog, issue_log)
        st.success(f"'{title}' বইটি সফলভাবে যুক্ত হয়েছে!")

# ৩. বই ইস্যু
elif menu == "📤 বই ইস্যু করুন":
  st.subheader("শিক্ষক বা শিক্ষার্থীকে বই প্রদান")
  available_books = (
      catalog[catalog["Available_Copies"] > 0] if not catalog.empty else pd.DataFrame()
  )

  if available_books.empty:
    st.warning("বর্তমানে ইস্যু করার মতো কোনো বই এভেলেবল নেই।")
  else:
    book_list = [
        f"{row['Book_ID']} - {row['Title']}"
        for _, row in available_books.iterrows()
    ]
    selected_book = st.selectbox("বই নির্বাচন করুন", book_list)
    borrower_name = st.text_input("গ্রহীতার নাম")
    role_id = st.text_input("আইডি / রোল / পদবী (শিক্ষক/শিক্ষার্থী)")
    days = st.number_input(
        "কত দিনের জন্য ইস্যু করা হচ্ছে?", min_value=1, value=7
    )

    if st.button("ইস্যু নিশ্চিত করুন"):
      book_id = selected_book.split(" - ")[0]
      catalog.loc[catalog["Book_ID"] == book_id, "Available_Copies"] -= 1

      issue_id = f"TX-{len(issue_log)+1:03d}"
      issue_date = datetime.now().strftime("%Y-%m-%d")
      return_deadline = (
          datetime.now() + timedelta(days=days)
      ).strftime("%Y-%m-%d")

      new_issue = pd.DataFrame([{
          "Issue_ID": issue_id,
          "Book_ID": book_id,
          "Borrower_Name": borrower_name,
          "Role_ID": role_id,
          "Issue_Date": issue_date,
          "Return_Deadline": return_deadline,
          "Status": "Issued",
      }])

      issue_log = pd.concat([issue_log, new_issue], ignore_index=True)
      save_data(catalog, issue_log)
      st.success(f"বই ইস্যু সম্পন্ন হয়েছে! জমার শেষ তারিখ: {return_deadline}")

# ৪. বই জমা
elif menu == "🔄 বই জমা নিন":
  st.subheader("ইস্যুকৃত বই ফেরত গ্রহণ")
  active_issues = (
      issue_log[issue_log["Status"] == "Issued"]
      if not issue_log.empty
      else pd.DataFrame()
  )

  if active_issues.empty:
    st.info("বর্তমানে কোনো বই ইস্যু করা নেই।")
  else:
    issue_list = [
        f"{row['Issue_ID']} - {row['Book_ID']} (গ্রহীতা: {row['Borrower_Name']})"
        for _, row in active_issues.iterrows()
    ]
    selected_issue = st.selectbox("ফেরত দেওয়া বই সিলেক্ট করুন", issue_list)

    if st.button("জমা কনফার্ম করুন"):
      iss_id = selected_issue.split(" - ")[0]
      book_id = active_issues.loc[
          active_issues["Issue_ID"] == iss_id, "Book_ID"
      ].values[0]

      issue_log.loc[issue_log["Issue_ID"] == iss_id, "Status"] = "Returned"
      catalog.loc[catalog["Book_ID"] == book_id, "Available_Copies"] += 1

      save_data(catalog, issue_log)
      st.success("বই সফলভাবে লাইব্রেরিতে জমা নেওয়া হয়েছে!")

# ৫. ইস্যু রেজিস্টার
elif menu == "📋 ইস্যু রেজিস্টার":
  st.subheader("সকল বই ইস্যু ও ফেরতের ইতিহাস")
  st.dataframe(issue_log, use_container_width=True)
