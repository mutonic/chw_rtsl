import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(page_title="eCHIS Dashboard", layout="wide")

# Load the synthetic dataset
file_path = "data/survey_filled_form_synthetic.xlsx"
df = pd.read_excel(file_path, sheet_name="CHW eCHIS")

# # Kobo API Credentials
# KOBO_API_URL = "https://kf.kobotoolbox.org/api/v2/assets/YOUR_FORM_ID/data/"
# KOBO_API_TOKEN = "YOUR_KOBO_API_TOKEN"

# # Function to fetch data from KoboToolbox
# def fetch_kobo_data():
#     headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}
#     response = requests.get(KOBO_API_URL, headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         return pd.DataFrame(data['results'])
#     else:
#         st.error("Failed to fetch data from KoboToolbox. Check API credentials and connection.")
#         return pd.DataFrame()

# # Load the dataset from KoboToolbox
# df = fetch_kobo_data()

# Normalize column names
df.columns = df.columns.str.strip()

# Convert submission time to datetime format
df['_submission_time'] = pd.to_datetime(df['_submission_time'], errors='coerce')
df['Submission Date'] = df['_submission_time'].dt.date

# Sidebar Navigation
st.sidebar.title("📊 eCHIS Dashboard")
st.sidebar.header("🔎 Filters")


# Gender Filter
gender_options = ["Both", "Gabo", "Gore"]
selected_gender = st.sidebar.radio("Filter by Gender", gender_options)

if selected_gender == "Both":
    df_filtered = df
elif selected_gender == "Gabo":
    df_filtered = df[df['Igitsina'] == 'Gabo']
elif selected_gender == "Gore":
    df_filtered = df[df['Igitsina'] == 'Gore']

# Date filtering
start_date = st.sidebar.date_input("Start Date", df_filtered['Submission Date'].min())
end_date = st.sidebar.date_input("End Date", df_filtered['Submission Date'].max())
if start_date and end_date:
    df_filtered = df_filtered[(df_filtered['Submission Date'] >= start_date) & (df_filtered['Submission Date'] <= end_date)]

st.sidebar.markdown("---")

# Main Dashboard Layout
st.title("📍 eCHIS Community Health Worker Dashboard")
st.markdown("---")

# Top Metrics Cards
st.markdown("## 🔹 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("📋 Total Forms Submitted", len(df_filtered))
col2.metric("👥 Unique CHWs Interviewed", df_filtered['Amazina y\'ufata amakuru'].nunique())
col3.metric("📆 Date Range", f"{df_filtered['Submission Date'].min()} - {df_filtered['Submission Date'].max()}")

# 📈 Form Submission Trend
st.markdown("## 🔹 Submission Trends")
df_trend = df_filtered.groupby('Submission Date').size().reset_index(name='Count')
fig = px.line(df_trend, x='Submission Date', y='Count', title='📈 Trend of Form Submissions Over Time', markers=True, text='Count')
fig.update_traces(textposition="top center")
st.plotly_chart(fig, use_container_width=True)

# 📊 Key Insights Section
st.markdown("## 🔹 Key Insights")
col1, col2 = st.columns(2)
gender_counts = df_filtered['Igitsina'].value_counts()
col1.markdown("### 🏥 Gender Distribution")
fig = px.bar(x=gender_counts.index, y=gender_counts.values, labels={'x': 'Gender', 'y': 'Count'}, title="Gender Distribution", text_auto=True)
col1.plotly_chart(fig)

data_accuracy_col = '1.7  Ese gukoresha eCHIS byagufashije gutanga/kubona amakuru yukuri?'
if data_accuracy_col in df_filtered.columns:
    col2.markdown("### ✅ eCHIS Data Accuracy Impact")
    fig = px.pie(df_filtered, names=data_accuracy_col, title="Utilization of eCHIS for Data Accuracy", hole=0.4)
    col2.plotly_chart(fig)

# Technical Challenges Summary
st.markdown("## 🔹 Technical Challenges in eCHIS")
col1, col2 = st.columns(2)
tech_challenges_col = '1.13 Niba ari yego, ni izihe mbogamizi cyangwa ibibazo uhura nabyo cyane?'
if tech_challenges_col in df_filtered.columns:
    tech_challenges_summary = df_filtered[tech_challenges_col].value_counts()
    total_tech_challenges = tech_challenges_summary.sum()
    col1.metric("⚠️ Total CHWs Reporting Technical Challenges in eCHIS", total_tech_challenges)
    fig = px.bar(x=tech_challenges_summary.index, y=tech_challenges_summary.values, title="Technical Challenges Faced", text_auto=True)
    col1.plotly_chart(fig)


# 📊 Aggregated Insights
st.markdown("## 📊 Aggregated Insights")

col1, col2 = st.columns(2)
digital_lit_col = "5.5 Ese eCHIS yongereye ubumenyi bwo gukoresha ikoranabuhanga mu bajyanama b’ ubuzima b'abagore?"

decision_col = "2.4 Niba ari Yego, ni kangahe ukoresha amakuru uhabwa n'imbonerahamwe mu gufata ibyemezo?"
if decision_col in df_filtered.columns:
    decision_summary = df_filtered[decision_col].value_counts()
    total_decision_making = decision_summary.sum()
    col1.metric("📊 Total CHWs Using eCHIS for Decision Making", total_decision_making)
    fig = px.bar(x=decision_summary.index, y=decision_summary.values, title="Decision Making Using eCHIS", text_auto=True)
    col1.plotly_chart(fig)

if digital_lit_col in df_filtered.columns:
    digital_lit_summary = df_filtered[digital_lit_col].value_counts()
    total_digital_lit = digital_lit_summary.sum()
    col2.metric("📱 Total CHWs Reporting eCHIS Influence on Digital Literacy", total_digital_lit)
    fig = px.bar(x=digital_lit_summary.index, y=digital_lit_summary.values, title="eCHIS Influence on Digital Literacy", text_auto=True)
    col2.plotly_chart(fig)



