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
st.title("Characteristics of CHWs interviewed")
st.markdown("## Number of CHWs interviewed by Health Centers")

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
        Villages=('group_lx1ft50/umudugudu', 'nunique'),
        CHWs=('group_lx1ft50/Amazina_y_umujyanama', 'nunique')
    ).reset_index()

    # Rename columns
    summary_df.columns = ['District', 'Health Center', 'Number of Villages', 'Number of CHWs']
    summary_df['District'] = summary_df['District'].str.upper()
    summary_df['Health Center'] = summary_df['Health Center'].str.upper()

    # Compute totals
    total_chws = summary_df['Number of CHWs'].sum()
    total_villages = summary_df['Number of Villages'].sum()

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

col1.markdown(f"""
    📋 **Total Number of Submissions**  
    # **{len(df_filtered)}**
""", unsafe_allow_html=True)

col2.markdown(f"""
    👥 **Unique CHWs Interviewed**  
    # **{df_filtered['group_lx1ft50/Amazina_y_umujyanama'].nunique()}**
""", unsafe_allow_html=True)

completion_rate = round((len(df_filtered)/144)*100,2)

col3.markdown(f"""
    📆 **Data Completion Rate**  
    # **{completion_rate}%**
""", unsafe_allow_html=True)

# Add space at the top
st.markdown("<br>", unsafe_allow_html=True)
# Add space at the top
st.markdown("<br>", unsafe_allow_html=True)
# Add space at the top
st.markdown("<br>", unsafe_allow_html=True)
### Line Chart
col1, col2 = st.columns(2)
# 📈 Form Submission Trend
col1.markdown("## 🔹Survey daily collection")

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

# Ensure date formatting is Day-Month-Year (without time)
fig.update_xaxes(
    tickformat="%d-%m-%Y",
    dtick="D1"
)

# Ensure text labels are visible and bold
fig.update_traces(
    textposition="top center",
    textfont=dict(size=14, color="white", family="Arial Black")
)

# Set the y-axis to start from zero explicitly
fig.update_yaxes(rangemode='tozero')

# Display the chart
col2.plotly_chart(fig, use_container_width=True)


# Number of CHWs by Gender
if gender_col in df_filtered.columns:
    gender_counts = df_filtered[gender_col].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    fig = px.bar(gender_counts, x='Gender', y='Count', title="🏥 Gender Distribution", text_auto=True)
    col1.plotly_chart(fig)

# 📊 **Module 1: System Management, integration, workload & CHW Performance**



st.markdown("## Module 1: System Management, integration, workload & CHW Performance")

# Column indicating if reporting was done on paper before eCHIS
# Columns definition

col1, col2 = st.columns(2)
paper_reporting_col = 'group_xc3oo49/_1_2_Niba_ari_Yego_n_yakorwaga_ku_mpapuro'
data_entry_col = 'group_xc3oo49/Ese_uburyo_bwo_kwinjiza_amakur'

if paper_reporting_col in df_filtered.columns and data_entry_col in df_filtered.columns:
    # Responses for those who changed reporting method (Yes)
    paper_reporting_responses = df_filtered[paper_reporting_col].dropna().str.split(" ").explode()
    response_counts = Counter(paper_reporting_responses)

    # Count those who answered "Oya" (No) on the data entry method change
    oya_count = df_filtered[data_entry_col].str.lower().value_counts().get('oya', 0)

    # Add 'Oya' responses explicitly
    response_counts['Oya'] = oya_count

    # Convert counts to DataFrame
    response_df = pd.DataFrame(response_counts.items(), columns=['Reporting_Method', 'Frequency']).sort_values(by='Frequency', ascending=False)

    # Bar chart visualization
    fig = px.bar(
        response_df,
        x='Reporting_Method',
        y='Frequency',
        title="Changes in Reporting Method with eCHIS Implementation (Including 'Oya' responses)",
        text='Frequency'
    )

    fig.update_layout(xaxis_title="Reporting Method", yaxis_title="Number of Respondents")

    # Display chart
    col1.plotly_chart(fig, use_container_width=True)

else:
    missing_cols = [col for col in [paper_reporting_col, data_entry_col] if col not in df_filtered.columns]
    col1.warning(f"Missing columns in dataset: {', '.join(missing_cols)}.")



# Data Accuracy
data_accuracy_col = 'group_xc3oo49/Ese_gukoresha_eCHIS_byongera_u'
if data_accuracy_col in df_filtered.columns:
    fig = px.pie(df_filtered, names=data_accuracy_col, title="Utilization of eCHIS improved data accuracy", hole=0.4)
    col2.plotly_chart(fig)

# Technical Challenges in eCHIS
tech_challenges_col = 'group_xc3oo49/Ni_izihe_mbogamizi_za_tekiniki'
if tech_challenges_col in df_filtered.columns:
    all_responses = df_filtered[tech_challenges_col].dropna().str.split(" ").explode()
    challenge_counts = Counter(all_responses)
    challenge_df = pd.DataFrame(challenge_counts.items(), columns=['Challenge', 'Count']).sort_values(by='Count', ascending=False)
    st.plotly_chart(px.bar(challenge_df, x='Challenge', y='Count', title="Technical Challenges in eCHIS", text='Count'))
    

# 📊 **Module 2: Utilization of eCHIS for Reporting**
st.markdown("## Module 2: Health Outcomes and Decision-Making")

col1, col2 = st.columns(2)

# Define column names
decision_making_col = 'group_ns1cq92/Hari_ibyemezo_wafashe_bishingi'
decision_frequency_col = 'group_ns1cq92/_2_4_Niba_ari_Yego_n_mu_gufata_ibyemezo'

if decision_making_col in df_filtered.columns and decision_frequency_col in df_filtered.columns:
    # Count "Yes" (Yego) and "No" (Oya) responses
    decision_counts = df_filtered[decision_making_col].str.lower().value_counts()

    # Count frequencies for those who answered "Yes" (Yego)
    frequency_counts = df_filtered[df_filtered[decision_making_col].str.lower() == 'yego'][decision_frequency_col].dropna().value_counts()

    # Merge "Oya" responses as a new category
    frequency_counts['Oya'] = decision_counts.get('oya', 0)

    # Convert to DataFrame
    frequency_df = pd.DataFrame(frequency_counts.items(), columns=['Frequency', 'Count'])

    # Translate Kinyarwanda responses
    frequency_translation = {
        "Burimunsi": "Daily",
        "Buricyumweru": "Weekly",
        "Burikwezi": "Monthly",
        "Rimwe na rimwe": "Occasionally",
        "Oya": "No Use"
    }
    frequency_df['Frequency'] = frequency_df['Frequency'].replace(frequency_translation)

    # Plot merged bar chart
    fig = px.bar(
        frequency_df,
        x='Frequency',
        y='Count',
        title="📊 Usage of eCHIS Data for Decision-Making",
        text='Count'
    )
    col1.plotly_chart(fig, use_container_width=True)

else:
    missing_cols = [col for col in [decision_making_col, decision_frequency_col] if col not in df_filtered.columns]
    col1.warning(f"Missing columns in dataset: {', '.join(missing_cols)}.")

# Define column names
info_timing_col = 'group_ns1cq92/Ese_kubona_amakuru_mu_gihe_nya'
service_satisfaction_col = 'group_ns1cq92/_2_7Niba_ari_Yego_Ni_ire_yawe_ya_serivisi'

if info_timing_col in df_filtered.columns and service_satisfaction_col in df_filtered.columns:
    # Count "Yes" (Yego) and "No" (Oya) responses
    info_timing_counts = df_filtered[info_timing_col].str.lower().value_counts()

    # Count satisfaction levels for those who answered "Yes" (Yego)
    satisfaction_counts = df_filtered[df_filtered[info_timing_col].str.lower() == 'yego'][service_satisfaction_col].dropna().value_counts()

    # Merge "Oya" responses as a new category
    satisfaction_counts['Oya'] = info_timing_counts.get('oya', 0)

    # Convert to DataFrame
    satisfaction_df = pd.DataFrame(satisfaction_counts.items(), columns=['Satisfaction Level', 'Count'])

    # Translate Kinyarwanda responses
    satisfaction_translation = {
        "Cyane": "Very Much",
        "Bihagije": "Quite a bit",
        "Bucye": "Somewhat",
        "Bucye cyane": "A little",
        "Oya": "No Use"
    }
    satisfaction_df['Satisfaction Level'] = satisfaction_df['Satisfaction Level'].replace(satisfaction_translation)

    # Plot merged bar chart
    fig = px.bar(
        satisfaction_df,
        x='Satisfaction Level',
        y='Count',
        title="📊 Service Satisfaction Based on Information Received on Time",
        text='Count'
    )
    col2.plotly_chart(fig, use_container_width=True)

else:
    missing_cols = [col for col in [info_timing_col, service_satisfaction_col] if col not in df_filtered.columns]
    col2.warning(f"Missing columns in dataset: {', '.join(missing_cols)}.")


# 📊 **Module 3: Decision Making & Service Delivery**
st.markdown("## Module 3: Decision Making & Service Delivery")

col1, col2 = st.columns(2)

# Define the column for decision-making
decision_col = "group_ix4mu45/Ese_uhura_n_imbogamizi_mu_gucu"

if decision_col in df_filtered.columns:
    # Count occurrences of "Yes" (Yego) and "No" (Oya)
    decision_summary = df_filtered[decision_col].str.lower().value_counts().reset_index()
    decision_summary.columns = ['Response', 'Count']

    # Translate Kinyarwanda responses
    response_translation = {
        "yego": "Yes",
        "oya": "No"
    }
    decision_summary['Response'] = decision_summary['Response'].replace(response_translation)

    # Create a Pie Chart
    fig = px.pie(
        decision_summary, 
        names='Response', 
        values='Count', 
        title="💊 Challenges in Requesting & Managing Medicine Stock",
        hole=0.4  # Donut-style
    )

    # Display Pie Chart
    col1.plotly_chart(fig, use_container_width=True)
else:
    col1.warning(f"Missing column in dataset: {decision_col}.")

# Define column for usage of eCHIS data
echis_usage_col = 'group_ix4mu45/_3_7_Amakuru_uhabwa_na_eCHIS_uy'

if echis_usage_col in df_filtered.columns:
    # Extract and split multiple responses
    all_responses = df_filtered[echis_usage_col].dropna().str.split(" ").explode()

    # Count occurrences of each usage type
    usage_counts = Counter(all_responses)

    # Convert to DataFrame
    usage_df = pd.DataFrame(usage_counts.items(), columns=['Usage', 'Count']).sort_values(by='Count', ascending=True)

    # Create a Horizontal Bar Chart for better readability
    fig = px.bar(
        usage_df, 
        y='Usage', 
        x='Count', 
        title="📊 Primary Uses of eCHIS Data",
        text='Count', 
        orientation='h'
    )

    # Display the chart
    col2.plotly_chart(fig, use_container_width=True)

else:
    col2.warning(f"Missing column in dataset: {echis_usage_col}.")

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

# Define column names
access_digital_col = 'group_ni9tc74/Ese_eCHIS_yongereye_icyigero_c'
digital_tool_level_col = 'group_ni9tc74/_5_2_Niba_ari_yego_Ni_rwego_rw_umudugudu'

if access_digital_col in df_filtered.columns and digital_tool_level_col in df_filtered.columns:
    # Count "Yes" (Yego) and "No" (Oya) responses
    access_counts = df_filtered[access_digital_col].str.lower().value_counts()

    # Count responses for those who answered "Yes" (Yego)
    tool_level_counts = df_filtered[df_filtered[access_digital_col].str.lower() == 'yego'][digital_tool_level_col].dropna().value_counts()

    # Merge "Oya" responses as a new category
    tool_level_counts['Oya'] = access_counts.get('oya', 0)

    # Convert to DataFrame
    tool_level_df = pd.DataFrame(tool_level_counts.items(), columns=['Access Level', 'Count'])

    # Plot merged bar chart
    fig = px.bar(
        tool_level_df,
        x='Access Level',
        y='Count',
        title="📊 Increase in Access to Digital Tools Among Female CHWs",
        text='Count'
    )
    col1.plotly_chart(fig, use_container_width=True)

else:
    missing_cols = [col for col in [access_digital_col, digital_tool_level_col] if col not in df_filtered.columns]
    col1.warning(f"Missing columns in dataset: {', '.join(missing_cols)}.")

# Define column names
digital_literacy_col = 'group_ni9tc74/_5_3_Ese_eCHIS_yaba_yarongereye'
internet_reliability_col = 'group_ni9tc74/_5_4_Niba_ari_yego_ni_esha_internet_yizewe'

if digital_literacy_col in df_filtered.columns and internet_reliability_col in df_filtered.columns:
    # Count "Yes" (Yego) and "No" (Oya) responses
    literacy_counts = df_filtered[digital_literacy_col].str.lower().value_counts()

    # Count responses for those who answered "Yes" (Yego)
    reliability_counts = df_filtered[df_filtered[digital_literacy_col].str.lower() == 'yego'][internet_reliability_col].dropna().value_counts()

    # Merge "Oya" responses as a new category
    reliability_counts['Oya'] = literacy_counts.get('oya', 0)

    # Convert to DataFrame
    reliability_df = pd.DataFrame(reliability_counts.items(), columns=['Digital Literacy Level', 'Count'])

    # Plot merged bar chart
    fig = px.bar(
        reliability_df,
        x='Digital Literacy Level',
        y='Count',
        title="📊 Increase in Digital Literacy Among Female CHWs",
        text='Count'
    )
    col2.plotly_chart(fig, use_container_width=True)

else:
    missing_cols = [col for col in [digital_literacy_col, internet_reliability_col] if col not in df_filtered.columns]
    col2.warning(f"Missing columns in dataset: {', '.join(missing_cols)}.")