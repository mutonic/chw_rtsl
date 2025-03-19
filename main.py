import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter

# Set Streamlit page configuration
st.set_page_config(page_title="eCHIS Dashboard", layout="wide")

# Kobo API Credentials
KOBO_API_URL = "https://kf.kobotoolbox.org/api/v2/assets/ahGnD6CC7JTsBbNFdsxLcS/data/?format=json"
KOBO_API_TOKEN = "6220f49a5232f4e03f14676d7f074d1fecf650ce"

# Function to fetch data from KoboToolbox
def fetch_kobo_data():
    headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}
    response = requests.get(KOBO_API_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "results" in data:
            df = pd.DataFrame(data["results"])
            return df if not df.empty else pd.DataFrame()
    st.error(f"Failed to fetch data: {response.status_code}")
    return pd.DataFrame()

# Load dataset
df = fetch_kobo_data()

# Data Preparation
if not df.empty:
    df.columns = df.columns.astype(str).str.strip()
    df['_submission_time'] = pd.to_datetime(df['_submission_time'], errors='coerce')
    df['Submission Date'] = df['_submission_time'].dt.date

# Sidebar - Filters
st.sidebar.title("📊 eCHIS Dashboard")
st.sidebar.header("🔎 Filters")

# Gender Filter
gender_col = "group_lx1ft50/Igitsina"
if gender_col in df.columns:
    df[gender_col] = df[gender_col].astype(str).str.lower().str.strip()
    selected_gender = st.sidebar.radio("Filter by Gender", ["Both", "Gabo", "Gore"])
    df_filtered = df if selected_gender == "Both" else df[df[gender_col] == selected_gender.lower()]
else:
    st.warning(f"Column '{gender_col}' not found.")
    df_filtered = df

# Date filter
if not df_filtered.empty:
    start_date = st.sidebar.date_input("Start Date", df_filtered['Submission Date'].min())
    end_date = st.sidebar.date_input("End Date", df_filtered['Submission Date'].max())
    df_filtered = df_filtered[(df_filtered['Submission Date'] >= start_date) & (df_filtered['Submission Date'] <= end_date)]

# Main Dashboard Layout
st.title("📍 eCHIS Monitoring Dashboard")
st.markdown("---")

# 📊 Summary Section
st.markdown("## Number of CHWs interviewed by Health centers")

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

    # Append the total row
    total_row = pd.DataFrame([['Total', '', total_villages, total_chws]], 
                              columns=summary_df.columns)
    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

    # Display the table correctly
    st.dataframe(summary_df)
    
else:
    st.warning("Some required columns are missing in the dataset.")

st.markdown("---")

# Top Metrics Cards
col1, col2, col3 = st.columns(3)
col1.metric("📋 Total Number of Submissions", len(df_filtered))
col2.metric("👥 Unique CHWs Interviewed", df_filtered['group_lx1ft50/Amazina_y_umujyanama'].nunique())
col3.metric("📆 Data Completion Rate", f"{round((len(df_filtered)/144)*100,2)}%")

# 📈 Form Submission Trend
st.markdown("## 🔹Survey daily collection")

# Ensure 'Submission Date' is in correct datetime format
df_filtered['Submission Date'] = pd.to_datetime(df_filtered['Submission Date'], errors='coerce').dt.date

# Group data correctly by Date (removing duplicates)
df_trend = df_filtered.groupby('Submission Date', as_index=False).size()

# Sort by date to prevent X-axis misalignment
df_trend = df_trend.sort_values(by='Submission Date')

# Format text labels to be bold
df_trend['size_bold'] = df_trend['size'].apply(lambda x: f"<b>{x}</b>")

# Create the line chart
fig = px.line(df_trend, x='Submission Date', y='size',
              title='📈 Trend of Form Submissions Over Time',
              markers=True, text='size_bold')

# Ensure date formatting is only Day-Month-Year (without time)
fig.update_xaxes(
    tickformat="%d-%m-%Y",
    dtick="D1"
)

# Ensure text labels are visible and bold
fig.update_traces(
    textposition="top center",
    textfont=dict(size=14, color="white", family="Arial Black")
)

# Display the chart
st.plotly_chart(fig, use_container_width=True)

# 📊 **Module 1: CHW Characteristics**
st.markdown("## Module 1: Characteristics of CHWs Interviewed")

col1, col2 = st.columns(2)

# Number of CHWs by Gender
if gender_col in df_filtered.columns:
    gender_counts = df_filtered[gender_col].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    fig = px.bar(gender_counts, x='Gender', y='Count', title="🏥 Gender Distribution", text_auto=True)
    col1.plotly_chart(fig)

# Data Accuracy
data_accuracy_col = 'group_xc3oo49/Ese_gukoresha_eCHIS_byongera_u'
if data_accuracy_col in df_filtered.columns:
    fig = px.pie(df_filtered, names=data_accuracy_col, title="Utilization of eCHIS for Data Accuracy", hole=0.4)
    col2.plotly_chart(fig)

# 📊 **Module 2: Utilization of eCHIS for Reporting**
st.markdown("## Module 2: Utilization of eCHIS for Reporting")

# Technical Challenges in eCHIS
tech_challenges_col = 'group_xc3oo49/Ni_izihe_mbogamizi_za_tekiniki'
if tech_challenges_col in df_filtered.columns:
    all_responses = df_filtered[tech_challenges_col].dropna().str.split(" ").explode()
    challenge_counts = Counter(all_responses)
    challenge_df = pd.DataFrame(challenge_counts.items(), columns=['Challenge', 'Count']).sort_values(by='Count', ascending=False)
    st.plotly_chart(px.bar(challenge_df, x='Challenge', y='Count', title="Technical Challenges in eCHIS", text='Count'))

# 📊 **Module 3: Decision Making & Service Delivery**
st.markdown("## Module 3: Decision Making & Service Delivery")

col1, col2 = st.columns(2)

decision_col = "group_ns1cq92/_2_4_Niba_ari_Yego_n_mu_gufata_ibyemezo"
if decision_col in df_filtered.columns:
    decision_summary = df_filtered[decision_col].value_counts()
    fig = px.bar(x=decision_summary.index, y=decision_summary.values, title="📊 Decision Making Using eCHIS", text_auto=True)
    col1.plotly_chart(fig)

# # 📊 **Module 4: Training & Support**
# Technical Challenges in eCHIS 4.2
st.markdown("## Module 4: Training & Support")

col1, col2 = st.columns(2)
training_satisfaction_col = "group_hl7oa32/_4_2_Niba_ari_yego_E_nyuze_ku_ruhe_rugero"
if training_satisfaction_col in df_filtered.columns:
    satisfaction_counts = df_filtered[training_satisfaction_col].value_counts().reset_index()
    satisfaction_counts.columns = ['Satisfaction Level', 'Count']
    
    fig = px.bar(satisfaction_counts, x='Satisfaction Level', y='Count',
                 title="Level of Satisfaction with eCHIS Training", text_auto=True)
    col1.plotly_chart(fig)

col1.markdown("---")

# Technical Challenges in eCHIS 4.4
training_needs_col = 'group_hl7oa32/Ni_ubuhe_bufasha_bwiyongera_bw'
if training_needs_col in df_filtered.columns:
    all_responses = df_filtered[training_needs_col].dropna().str.split(" ").explode()
    challenge_counts = Counter(all_responses)
    challenge_df = pd.DataFrame(challenge_counts.items(), columns=['Challenge', 'Count']).sort_values(by='Count', ascending=False)
    col2.plotly_chart(px.bar(challenge_df, x='Challenge', y='Count', title="Technical Challenges in eCHIS", text='Count'))

col2.markdown("---")

# 📊 **Module 5: Digital Literacy & Women's Health**
st.markdown("## Module 5: Digital Literacy & Women's Health")

col1, col2 = st.columns(2)
digital_lit_col = "group_ni9tc74/Ese_eCHIS_yaba_yaragize_icyo_i"
if digital_lit_col in df_filtered.columns:
    fig = px.bar(df_filtered, x=digital_lit_col, title="Impact of eCHIS on Digital Literacy")
    col1.plotly_chart(fig)

col1.markdown("---")

# ✅ **This version ensures better layout, clarity, and structured insights!**