import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from collections import Counter

# Set Streamlit page configuration
st.set_page_config(page_title="eCHIS Dashboard", layout="wide")

# Load the synthetic dataset
# file_path = "data/survey_filled_form_synthetic.xlsx"
# df = pd.read_excel(file_path, sheet_name="CHW eCHIS")

# # Kobo API Credentials
KOBO_API_URL = "https://kf.kobotoolbox.org/api/v2/assets/ahGnD6CC7JTsBbNFdsxLcS/data/?format=json"
KOBO_API_TOKEN = "6220f49a5232f4e03f14676d7f074d1fecf650ce"

# Function to fetch data from KoboToolbox
def fetch_kobo_data():
    headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}
    response = requests.get(KOBO_API_URL, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if "results" in data:
                df = pd.DataFrame(data["results"])
                if df.empty:
                    st.warning("Kobo API returned an empty dataset.")
                return df
            else:
                st.error("Invalid response format: 'results' key not found.")
                st.write("Raw response:", data)  # Debugging: show response
                return pd.DataFrame()
        except requests.exceptions.JSONDecodeError:
            st.error("Failed to decode JSON. Response is not in JSON format.")
            st.write("Raw response:", response.text)  # Show raw response for debugging
            return pd.DataFrame()
    else:
        st.error(f"Failed to fetch data: {response.status_code} - {response.text}")
        return pd.DataFrame()

# Load the dataset from KoboToolbox
df = fetch_kobo_data()

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
    df_filtered = df[df['group_lx1ft50/Igitsina'] == 'Gabo']
elif selected_gender == "Gore":
    df_filtered = df[df['group_lx1ft50/Igitsina'] == 'Gore']

# Date filtering
start_date = st.sidebar.date_input("Start Date", df_filtered['Submission Date'].min())
end_date = st.sidebar.date_input("End Date", df_filtered['Submission Date'].max())
if start_date and end_date:
    df_filtered = df_filtered[(df_filtered['Submission Date'] >= start_date) & (df_filtered['Submission Date'] <= end_date)]

st.sidebar.markdown("---")

# Main Dashboard Layout
st.title("📍 eCHIS Community Health Worker Dashboard")
st.markdown("---")

# 📊 Summary Section
st.markdown("## 🔹 Summary Table")

# Check if required columns exist in the dataset
required_columns = [
    'group_lx1ft50/akarere', 
    'group_lx1ft50/ikigonderabuzima', 
    'group_lx1ft50/Amazina_y_umujyanama', 
    'group_lx1ft50/umudugudu'
]

if all(col in df_filtered.columns for col in required_columns):
    # Group and aggregate data
    summary_df = df_filtered.groupby(
        ['group_lx1ft50/akarere', 'group_lx1ft50/ikigonderabuzima']
    ).agg(
        N_CHW=('group_lx1ft50/Amazina_y_umujyanama', 'nunique'),
        N_Villages=('group_lx1ft50/umudugudu', 'nunique')
    ).reset_index()

    # Rename columns
    summary_df.columns = ['District', 'Health Center', 'N° of CHWs', 'N° of Villages']

    # Compute totals
    total_chws = summary_df['N° of CHWs'].sum()
    total_villages = summary_df['N° of Villages'].sum()

    # Append the total row with bold formatting
    total_row = pd.DataFrame([['**Total**', '', total_villages], f'**{total_chws}**'], 
                              columns=summary_df.columns)
    
    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

    # Display the table correctly with Markdown formatting
    st.markdown(summary_df.to_markdown(index=False), unsafe_allow_html=True)
    
else:
    st.warning("Some required columns are missing in the dataset.")

st.markdown("---")

# Top Metrics Cards
st.markdown("## 🔹 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("📋 Total Forms Submitted", len(df_filtered))
col2.metric("👥 Unique CHWs Interviewed", df_filtered['group_lx1ft50/Amazina_y_umujyanama'].nunique())
col3.metric("📆 Data Completion Rate", f"{(total_villages/144)*100}%")

# 📈 Form Submission Trend
st.markdown("## 🔹 Submission Trends")
df_trend = df_filtered.groupby('Submission Date').size().reset_index(name='Count')
fig = px.line(df_trend, x='Submission Date', y='Count', title='📈 Trend of Form Submissions Over Time', markers=True, text='Count')
fig.update_traces(textposition="top center")
st.plotly_chart(fig, use_container_width=True)

# 📊 Key Insights Section
st.markdown("## 🔹 Key Insights")
col1, col2 = st.columns(2)
gender_counts = df_filtered['group_lx1ft50/Igitsina'].value_counts()
col1.markdown("### 🏥 Gender Distribution")
fig = px.bar(x=gender_counts.index, y=gender_counts.values, labels={'x': 'Gender', 'y': 'Count'}, title="Gender Distribution", text_auto=True)
col1.plotly_chart(fig)

data_accuracy_col = 'group_xc3oo49/Ese_gukoresha_eCHIS_byongera_u'
if data_accuracy_col in df_filtered.columns:
    col2.markdown("### ✅ eCHIS Data Accuracy Impact")
    fig = px.pie(df_filtered, names=data_accuracy_col, title="Utilization of eCHIS for Data Accuracy", hole=0.4)
    col2.plotly_chart(fig)

# Technical Challenges Summary
st.markdown("## 🔹 Technical Challenges in eCHIS")
col1, col2 = st.columns(2)
tech_challenges_col = 'group_xc3oo49/Ni_izihe_mbogamizi_za_tekiniki'

if tech_challenges_col in df_filtered.columns:
    # Split multiple-answer responses into separate entries
    all_responses = df_filtered[tech_challenges_col].dropna().str.split(" ").explode()
    challenge_counts = Counter(all_responses)
    challenge_df = pd.DataFrame(challenge_counts.items(), columns=['Challenge', 'Count']).sort_values(by='Count', ascending=False)
    total_tech_challenges = challenge_df['Count'].sum()
    
    col1.metric("⚠️ Total CHWs Reporting Technical Challenges in eCHIS", total_tech_challenges)
    fig = px.bar(challenge_df, x='Challenge', y='Count', title="Technical Challenges Faced", text_auto=True)
    col1.plotly_chart(fig)


# 📊 Aggregated Insights
st.markdown("## 📊 Aggregated Insights")

col1, col2 = st.columns(2)


decision_col = "group_ns1cq92/_2_4_Niba_ari_Yego_n_mu_gufata_ibyemezo"
if decision_col in df_filtered.columns:
    decision_summary = df_filtered[decision_col].value_counts()
    total_decision_making = decision_summary.sum()
    col1.metric("📊 Total CHWs Using eCHIS for Decision Making", total_decision_making)
    fig = px.bar(x=decision_summary.index, y=decision_summary.values, title="Decision Making Using eCHIS", text_auto=True)
    col1.plotly_chart(fig)

digital_lit_col = "group_ni9tc74/Ese_eCHIS_yaba_yaragize_icyo_i"
if digital_lit_col in df_filtered.columns:
    digital_lit_summary = df_filtered[digital_lit_col].value_counts()
    total_digital_lit = digital_lit_summary.sum()
    col2.metric("📱 Total CHWs Reporting eCHIS Influence on Digital Literacy", total_digital_lit)
    fig = px.bar(x=digital_lit_summary.index, y=digital_lit_summary.values, title="eCHIS Influence on Digital Literacy", text_auto=True)
    col2.plotly_chart(fig)



