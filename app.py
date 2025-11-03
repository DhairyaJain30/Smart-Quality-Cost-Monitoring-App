# ============================================
# SMART QUALITY COST MONITORING DASHBOARD
# ============================================

import os
import pandas as pd
import streamlit as st
import plotly.express as px
from openai import OpenAI
from fpdf import FPDF
import time
import datetime
import plotly.io as pio
from dotenv import load_dotenv

# --- CONFIG & THEMING ---
load_dotenv()

DATA_FILE = "quality_data.csv"
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state["data"] = pd.read_csv(DATA_FILE)
    else:
        st.session_state["data"] = pd.DataFrame(columns=["Month", "Category", "Cost", "Description"])

st.set_page_config(page_title="Smart Quality Dashboard", page_icon="📊", layout="wide")
pio.templates.default = "seaborn"  # professional chart color theme

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
        .main {
            background-color: #121212;
            padding: 2rem;
        }
        .title-container {
            background: linear-gradient(90deg, #0f172a, #000000);
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
            text-align: center;
        }
        .title-container h1 {
            font-size: 2.3rem;
            margin-bottom: 0;
        }
        .title-container p {
            font-size: 1rem;
            opacity: 0.9;
        }
        [data-testid="stMetricValue"] {
            color: #00bcd4;  
            font-weight: 700;
        }
        .suggestion-box {
            background-color: #fff;
            border-left: 5px solid #2563eb;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class='title-container'>
    <h1>📊 Smart Quality Cost Monitoring Dashboard</h1>
    <p>Analyze, track, and improve your quality costs using TQM principles & AI insights.</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2966/2966484.png", width=80)
st.sidebar.title("🔧 Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["📂 Upload & Add Data", "📈 Dashboard & KPIs", "🤖 AI Suggestions", "🧾 Reports"]
)
st.sidebar.markdown("---")
st.sidebar.caption("• TQM Project 2025")
# --- OPENAI SETUP ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- INITIALIZE DATA ---
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(columns=["Month", "Category", "Cost", "Description"])
df = st.session_state["data"]

# ============================================
# PAGE 1: UPLOAD & ADD DATA
# ============================================
if page == "📂 Upload & Add Data":
    st.header("📤 Upload or Add Quality Cost Data")

    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        uploaded_df = pd.read_csv(uploaded_file)
        # Merge with existing session data
        df = pd.concat([st.session_state["data"], uploaded_df], ignore_index=True)
        df = df.drop_duplicates().reset_index(drop=True)
        st.session_state["data"] = df
        df.to_csv(DATA_FILE, index=False)  # 🔹 save merged data
        st.success("✅ File uploaded and merged successfully!")
    else:
        df = st.session_state["data"]

    st.markdown("### ➕ Add New Record")
    with st.form("add_record_form"):
        month = st.selectbox("Month", ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
        category = st.selectbox("Category", ["Prevention", "Appraisal", "Internal Failure", "External Failure"])
        cost = st.number_input("Cost (₹)", min_value=0)
        description = st.text_input("Description", placeholder="e.g. Training session, warranty claims...")
        submitted = st.form_submit_button("Add Record")

    if submitted:
        new_entry = pd.DataFrame([[month, category, cost, description]], columns=["Month", "Category", "Cost", "Description"])
        df = pd.concat([st.session_state["data"], new_entry], ignore_index=True)
        df = df.drop_duplicates().reset_index(drop=True)
        st.session_state["data"] = df
        df.to_csv(DATA_FILE, index=False)  # 🔹 permanently save
        
        with st.spinner("Saving your record..."):
            time.sleep(0.5)
        st.success("✅ Record added successfully!")
        df.to_csv("quality_data.csv", index=False)
# ============================================
# PAGE 2: DASHBOARD & KPIs
# ============================================
elif page == "📈 Dashboard & KPIs":
    st.header("📈 Quality Cost Dashboard")
    df = st.session_state["data"]
    if not df.empty:
        summary = df.groupby("Category")["Cost"].sum().reset_index()

        st.subheader("📊 Key Quality Performance Indicators (KPIs)")
        prevention = summary.loc[summary['Category']=='Prevention', 'Cost'].sum()
        appraisal = summary.loc[summary['Category']=='Appraisal', 'Cost'].sum()
        internal = summary.loc[summary['Category']=='Internal Failure', 'Cost'].sum()
        external = summary.loc[summary['Category']=='External Failure', 'Cost'].sum()

        COGQ, COPQ = prevention + appraisal, internal + external
        total = COGQ + COPQ

        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Cost of Good Quality", f"₹{COGQ:,.0f}")
        col2.metric("⚠️ Cost of Poor Quality", f"₹{COPQ:,.0f}")
        col3.metric("💰 Total Quality Cost", f"₹{total:,.0f}")

        kpi_df = pd.DataFrame({"Category": ["Good Quality (COGQ)", "Poor Quality (COPQ)"],
                               "Cost": [COGQ, COPQ]})
        fig_kpi = px.bar(kpi_df, x="Category", y="Cost", color="Category",
                         text_auto=True, title="COGQ vs COPQ Comparison",
                         color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_kpi, use_container_width=True)
        st.session_state["fig_kpi"] = fig_kpi 
        st.subheader("🔹 Cost Breakdown by Category")
        fig_pie = px.pie(summary, names="Category", values="Cost",
                         color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📉 Monthly Trend")
        # Define correct month order
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

        monthly = (
            df.groupby("Month")["Cost"]
            .sum()
            .reindex(month_order)        # Reorder rows by month
            .reset_index()
            .dropna(subset=["Cost"])     # Remove empty months
        )

        fig_line = px.line(
            monthly,
            x="Month",
            y="Cost",
            markers=True,
            title="Total Quality Cost per Month",
            line_shape="linear"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No data available. Please upload or add some records first.")

# ============================================
# PAGE 3: AI SUGGESTIONS
# ============================================
elif page == "🤖 AI Suggestions":
    st.header("🧠 AI-Based Quality Improvement Suggestions")

    if df.empty:
        st.warning("Please upload or add data first.")
    else:
        summary = df.groupby("Category")["Cost"].sum().reset_index()
        summary_text = (
            f"Prevention: ₹{summary.loc[summary['Category']=='Prevention', 'Cost'].sum()}, "
            f"Appraisal: ₹{summary.loc[summary['Category']=='Appraisal', 'Cost'].sum()}, "
            f"Internal Failure: ₹{summary.loc[summary['Category']=='Internal Failure', 'Cost'].sum()}, "
            f"External Failure: ₹{summary.loc[summary['Category']=='External Failure', 'Cost'].sum()}."
        )

        if st.button("Generate AI Suggestions"):
            prompt = f"""
                You are a professional Total Quality Management (TQM) consultant reviewing this company's cost data:
                {summary_text}

                Based on this information, write 3–4 short, data-driven recommendations to help management
                reduce total quality cost next month. Your response should:
                - Be concise (under 120 words total)
                - Sound professional and personalized, not generic
                - Reflect TQM principles like continuous improvement, prevention focus, and customer satisfaction
                - Mention specific cost trends if relevant (e.g., if prevention cost is low, recommend increasing it)

                Format the response in clean bullet points with short reasoning for each suggestion.
                """
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6
                )
                suggestions = response.choices[0].message.content
                st.markdown("---")
                st.markdown(f"<div class='suggestion-box'>{suggestions.replace('*', '•')}</div>",
                            unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================
# PAGE 4: REPORTS
# ============================================
elif page == "🧾 Reports":
    st.header("📋 AI-Generated Monthly Quality Report")

    if df.empty:
        st.warning("Please upload or add data first.")
    else:
        summary = df.groupby("Category")["Cost"].sum().reset_index()
        COGQ = summary.loc[summary['Category']=='Prevention', 'Cost'].sum() + summary.loc[summary['Category']=='Appraisal', 'Cost'].sum()
        COPQ = summary.loc[summary['Category']=='Internal Failure', 'Cost'].sum() + summary.loc[summary['Category']=='External Failure', 'Cost'].sum()
        total_cost = COGQ + COPQ

        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        available_months = [m for m in month_order if m in df["Month"].unique()]
        selected_month = st.selectbox("Select month for report", available_months)

        if st.button("Generate Monthly Report"):
            month_data = df[df["Month"] == selected_month]
            month_total = month_data["Cost"].sum()
            month_trend = df.groupby("Month")["Cost"].sum().reset_index().tail(3)

            summary_text = (
                f"Report for {selected_month}:\n"
                f"Total Quality Cost = ₹{month_total:,.0f}\n\n"
                f"Recent 3-month trend:\n{month_trend.to_string(index=False)}\n"
                f"COGQ = ₹{COGQ:,.0f}, COPQ = ₹{COPQ:,.0f}, Total = ₹{total_cost:,.0f}."
            )

            prompt = f"""
            You are a Quality Manager preparing a report for {selected_month}.
            Based on this data:
            {summary_text}

            Write a short (around 150 words) report highlighting:
            - This month’s quality cost performance
            - Trend compared to previous months
            - Recommendations for improvement next month
            Keep it professional, concise, and insights-focused.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                st.session_state["report"] = response.choices[0].message.content
                st.success("✅ Monthly report generated successfully!")
                st.markdown(f"<div class='suggestion-box'>{st.session_state['report']}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating report: {e}")

        # --- PDF EXPORT ---
        st.subheader("📥 Export Monthly Quality Report")
        if st.button("Download PDF Report"):
            if "report" in st.session_state:
                st.session_state["report"] = st.session_state["report"].replace("₹", "Rs.")

            if "report" not in st.session_state:
                st.warning("Generate the report first.")
            else:
                # Save KPI chart image
                kpi_chart_path = "kpi_chart.png"
                fig_to_use = st.session_state.get("fig_kpi", None)
                if fig_to_use:
                    pio.write_image(fig_to_use, kpi_chart_path, format="png")
                else:
                    st.warning("⚠️ Please visit the Dashboard page first to generate KPI chart.")
                    st.stop()

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Monthly Quality Performance Report", ln=True, align="C")
                pdf.ln(8)

                pdf.set_font("Arial", '', 12)
                today = datetime.date.today().strftime("%B %Y")
                pdf.cell(0, 10, f"Date: {today}", ln=True)
                pdf.ln(5)

                pdf.multi_cell(0, 8, f"COGQ: Rs.{COGQ:,.0f}\nCOPQ: Rs.{COPQ:,.0f}\nTotal Cost: Rs.{total_cost:,.0f}\n")
                pdf.ln(4)
                pdf.set_font("Arial", 'B', 13)
                pdf.cell(0, 10, "KPI Comparison Chart:", ln=True)
                pdf.image(kpi_chart_path, x=25, y=None, w=160)
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 13)
                pdf.cell(0, 10, "AI-Generated Insights:", ln=True)
                pdf.set_font("Arial", '', 12)
                safe_report = st.session_state["report"].replace("₹", "Rs.")
                pdf.multi_cell(0, 8, safe_report)

                pdf.ln(5)

                pdf.cell(0, 10, "Generated by Smart Quality Cost Monitoring Dashboard", ln=True, align="C")

                pdf.output("Monthly_Quality_Report.pdf")
                with open("Monthly_Quality_Report.pdf", "rb") as f:
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=f,
                        file_name="Monthly_Quality_Report.pdf",
                        mime="application/pdf"
                    )
