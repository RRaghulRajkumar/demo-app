import streamlit as st
import psycopg2
import datetime
import pandas as pd
import plotly.express as px
from twilio.rest import Client

# Database connection
def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="subscription_db",
        user="postgres",
        password="password18",
        port="5432"
    )

# Initialize database
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            dob DATE,
            subscription_type VARCHAR(50),
            subscription_start DATE,
            subscription_end DATE,
            payment_status BOOLEAN,
            amount_paid NUMERIC(10,2),
            membership_status VARCHAR(20) DEFAULT 'active'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id SERIAL PRIMARY KEY,
            plan_name VARCHAR(100),
            duration_months INT,
            price NUMERIC(10,2)
        )
    """)
    conn.commit()
    conn.close()

# Register Member
def register_member(name, email, phone, address, dob, subscription_type, months, payment_status, amount_paid):
    conn = connect_db()
    cursor = conn.cursor()
    subscription_start = datetime.date.today()
    subscription_end = subscription_start + datetime.timedelta(days=30*months)
    cursor.execute("""
        INSERT INTO members (name, email, phone, address, dob, subscription_type, subscription_start, subscription_end, payment_status, amount_paid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, email, phone, address, dob, subscription_type, subscription_start, subscription_end, payment_status, amount_paid))
    conn.commit()
    conn.close()
    return subscription_end

# Fetch Active Subscriptions
def get_active_subscriptions():
    conn = connect_db()
    df = pd.read_sql("SELECT * FROM members WHERE subscription_end >= CURRENT_DATE AND membership_status='active'", conn)
    conn.close()
    return df

# Fetch Monthly Revenue
def get_monthly_revenue():
    conn = connect_db()
    df = pd.read_sql("""
        SELECT DATE_TRUNC('month', subscription_start) AS month, SUM(amount_paid) AS revenue
        FROM members WHERE payment_status = TRUE GROUP BY month ORDER BY month
    """, conn)
    conn.close()
    return df

# Fetch Membership Trends
def get_membership_trends():
    conn = connect_db()
    df = pd.read_sql("""
        SELECT subscription_type, COUNT(*) AS count
        FROM members GROUP BY subscription_type
    """, conn)
    conn.close()
    return df

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Subscription Management Dashboard")
init_db()

# Layout
col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.subheader("📝 Register New Member")
        with st.form("subscription_form"):
            name = st.text_input("👤 Name")
            email = st.text_input("📧 Email")
            phone = st.text_input("📞 Phone Number")
            address = st.text_area("🏠 Address")
            dob = st.date_input("🎂 Date of Birth")
            subscription_type = st.selectbox("📦 Subscription Type", ["Gym", "Tiffin Service", "SaaS"])
            months = st.selectbox("⏳ Subscription Duration (Months)", [1, 2, 3, 6, 12])
            payment_status = st.checkbox("💰 Payment Completed")
            amount_paid = st.number_input("💵 Amount Paid", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("✅ Subscribe")

        if submit:
            subscription_end = register_member(name, email, phone, address, dob, subscription_type, months, payment_status, amount_paid)
            st.success(f"🎉 Subscription activated until {subscription_end}")

with col2:
    with st.container():
        st.subheader("📈 Dashboard Metrics")
        active_df = get_active_subscriptions()
        st.metric("📌 Total Active Subscriptions", len(active_df))

        revenue_df = get_monthly_revenue()
        st.subheader("💰 Monthly Revenue Report")
        st.line_chart(revenue_df.set_index("month"))

        trend_df = get_membership_trends()
        st.subheader("📊 Membership Trends")
        st.bar_chart(trend_df.set_index("subscription_type"))

        pie_chart = px.pie(trend_df, names='subscription_type', values='count', title='📌 Subscription Distribution')
        st.plotly_chart(pie_chart)

st.subheader("📂 Export Data")
st.download_button("📥 Download Active Subscriptions", active_df.to_csv(index=False), "active_subscriptions.csv", "text/csv")
st.download_button("📥 Download Revenue Report", revenue_df.to_csv(index=False), "monthly_revenue.csv", "text/csv")
st.download_button("📥 Download Membership Trends", trend_df.to_csv(index=False), "membership_trends.csv", "text/csv")