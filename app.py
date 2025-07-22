import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Paustikk Switch's - Subscription Analytics Dashboard", layout="wide")

# ========== File Upload ==========
with st.sidebar:
    st.title("🔍 Filters")
    uploaded_file = st.file_uploader(
        "Upload a data file (.xlsx only)", type=["xlsx"], help="Upload your latest datasheet here."
    )

# Load Data
@st.cache_data
def load_data():
    df = pd.read_excel("PS_Data.xlsx")
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    df['Month'] = pd.to_datetime(df['Start_Date']).dt.to_period('M').astype(str)
    return df

df = load_data()

# Sidebar: Global Filters (NO Status filter)
with st.sidebar:
    st.title("🔍 Filters")
    plan_types = st.multiselect(
        "Select Plan Types:",
        options=df['Plan_Type'].unique(),
        default=list(df['Plan_Type'].unique())
    )
    meal_types = st.multiselect(
        "Select Meal Frequency:",
        options=df['Meal_Frequency'].unique(),
        default=list(df['Meal_Frequency'].unique())
    )
    min_price, max_price = int(df["Total_Price"].min()), int(df["Total_Price"].max())
    price_slider = st.slider(
        "Total Price Range (INR):",
        min_price, max_price, (min_price, max_price), step=500
    )
    st.write("")

# Filter DataFrame
filtered = df[
    df['Plan_Type'].isin(plan_types) &
    df['Meal_Frequency'].isin(meal_types) &
    (df["Total_Price"].between(*price_slider))
].copy()

# Tabs for Macro, Micro, and Custom Analysis
tabs = st.tabs([
    "📈 Macro Overview", "🔍 Micro Insights", "📊 Plan & Revenue Deep-dive", "🗂️ Raw Data"
])

# ==== 1. Macro Overview Tab ====
with tabs[0]:
    st.markdown(
        "<h1 style='text-align: center; color: #0D8661; font-size: 2.6rem; font-weight: 700;'>🍱 Paushtikk Switch: Evolve Everyday</h1>",
        unsafe_allow_html=True
    )
    st.title("📈 Macro Business Overview")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Subscribers", filtered['Customer_ID'].nunique())
    kpi2.metric("Total Revenue (INR)", f"{filtered['Total_Price'].sum():,.0f}")
    kpi3.metric("Avg. Revenue / Customer", f"{filtered['Total_Price'].mean():,.0f}")
    st.divider()

    st.markdown("""
**1.1. Subscriber Growth Over Time**  
Shows how subscriber sign-ups and revenue trend across months.
    """)
    by_month = (
        filtered.groupby('Month')
        .agg(Unique_Customers=('Customer_ID', 'nunique'), Total_Revenue=('Total_Price', 'sum'))
        .reset_index()
    )
    fig1 = px.bar(
        by_month,
        x='Month',
        y='Unique_Customers',
        title="New Subscribers Per Month",
        labels={'Unique_Customers': 'Number of Unique Customers', 'Month': 'Month'}
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("""
**1.2. Monthly Revenue Trend**  
Reveals monthly revenue performance to spot peaks & dips.
    """)
    fig2 = px.line(
        by_month, x='Month', y='Total_Revenue',
        markers=True, title="Monthly Revenue (INR)",
        labels={'Total_Revenue': 'Total Revenue (INR)', 'Month': 'Month'}
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
**1.3. Top Meal Frequencies**  
See which meal combinations drive most of the business.
    """)
    meal_freq_counts = (
        filtered['Meal_Frequency']
        .value_counts()
        .reset_index()
    )
    meal_freq_counts.columns = ['Meal_Frequency', 'Count']

    if not meal_freq_counts.empty:
        fig3 = px.bar(
            meal_freq_counts,
            x='Meal_Frequency',
            y='Count',
            labels={'Meal_Frequency': 'Meal Frequency', 'Count': 'Count'},
            title="Meal Plan Popularity"
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No data to display for Meal Plan Popularity. Try adjusting your filters.")

    st.markdown("""
**1.4. Revenue by Meal Frequency**  
Shows average order value by each meal plan type.
    """)
    st.plotly_chart(
        px.box(
            filtered,
            x='Meal_Frequency',
            y='Total_Price',
            title="Order Value by Meal Frequency",
            labels={'Meal_Frequency': 'Meal Frequency', 'Total_Price': 'Order Value (INR)'}
        ),
        use_container_width=True
    )

# ==== 2. Micro Insights Tab ====
with tabs[1]:
    st.title("🔍 Micro-Customer Insights")

    st.markdown("""
**2.1. Top 10 Customers by Spend**  
Know your highest value subscribers.
    """)
    top10 = (
        filtered.groupby(['Customer_ID', 'Customer_Name'])
        .agg(Total_Spend=('Total_Price', 'sum'))
        .sort_values('Total_Spend (INR)', ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top10, use_container_width=True)


    st.markdown("""
**2.2. Plan Length vs. Price**  
See how plan duration impacts customer spend.
    """)
    st.plotly_chart(
        px.scatter(
            filtered,
            x='Duration_Days',
            y='Total_Price',
            title="Plan Duration vs. Spend",
            labels={'Duration_Days': 'Duration (Days)', 'Total_Price': 'Spend (INR)'}
        ),
        use_container_width=True
    )

    st.markdown("""
**2.3. Price Range Distribution**  
Analyze customer segments by spend tier.
    """)
    st.plotly_chart(
        px.histogram(
            filtered,
            x='Total_Price',
            nbins=20,
            title="Customer Spend Histogram",
            labels={'Total_Price': 'Total Spend (INR)'}
        ),
        use_container_width=True
    )

    st.markdown("""
**2.4. Cohort Retention Table**  
Assess repeat rates for customers by first month joined.
    """)
    first = (
        df.groupby('Customer_ID')['Start_Date'].min()
        .reset_index()
    )
    first['CohortMonth'] = pd.to_datetime(first['Start_Date']).dt.to_period('M').astype(str)
    cohort = (
        first.groupby('CohortMonth')
        .agg(New_Customers=('Customer_ID', 'count'))
        .reset_index()
    )
    st.dataframe(cohort, use_container_width=True)

# ==== 3. Plan & Revenue Deep-dive Tab ====
with tabs[2]:
    st.title("📊 Plan, Meal, and Revenue Deep-dive")

    st.markdown("""
**3.1. Revenue by Plan Type**  
Find out which plan types earn the most for your business.
    """)
    revenue_by_plan = (
        filtered.groupby('Plan_Type')
        .agg(Total_Revenue=('Total_Price', 'sum'))
        .reset_index()
    )
    st.plotly_chart(
        px.bar(
            revenue_by_plan,
            x='Plan_Type',
            y='Total_Revenue',
            title="Total Revenue by Plan Type",
            labels={'Plan_Type': 'Plan Type', 'Total_Revenue': 'Total Revenue (INR)'}
        ),
        use_container_width=True
    )

    st.markdown("""
**3.2. Plan Popularity by Frequency**  
Matrix of plan type vs. meal frequency.
    """)
    plan_freq = pd.crosstab(filtered['Plan_Type'], filtered['Meal_Frequency'])
    st.dataframe(plan_freq, use_container_width=True)

    st.markdown("""
**3.3. Customer Distribution by Duration**  
Visualize spread of short, medium, long-duration plans.
    """)
    bins = [0, 7, 15, 31, 100]
    labels = ["0-7 days", "8-15 days", "16-30 days", "31+ days"]
    filtered['Duration_Category'] = pd.cut(
        filtered['Duration_Days'],
        bins=bins,
        labels=labels,
        right=False
    )
    st.plotly_chart(
        px.pie(
            filtered,
            names='Duration_Category',
            title="Plan Duration Segments"
        ),
        use_container_width=True
    )

    st.markdown("""
**3.4. Revenue by Duration Category**  
Which duration buckets are most profitable?
    """)
    rev_by_dur = (
        filtered.groupby('Duration_Category')['Total_Price']
        .sum()
        .reset_index()
    )
    st.plotly_chart(
        px.bar(
            rev_by_dur,
            x='Duration_Category',
            y='Total_Price',
            title="Revenue by Duration",
            labels={'Duration_Category': 'Duration Category', 'Total_Price': 'Revenue (INR)'}
        ),
        use_container_width=True
    )

    st.markdown("""
**3.5. Most Popular Combinations**  
Discover top Plan + Meal combos.
    """)
    combos = (
        filtered.groupby(['Plan_Type', 'Meal_Frequency'])
        .size()
        .reset_index(name='Count')
        .sort_values('Count', ascending=False)
        .head(10)
    )
    st.dataframe(combos, use_container_width=True)

    st.markdown("""
**3.6. Heatmap: Plan Type vs. Meal Frequency**  
Pinpoint where your growth is coming from.
    """)
    pivot2 = pd.pivot_table(
        filtered,
        values='Customer_ID',
        index='Plan_Type',
        columns='Meal_Frequency',
        aggfunc='count',
        fill_value=0
    )
    st.plotly_chart(
        px.imshow(
            pivot2,
            text_auto=True,
            aspect='auto',
            title="Plan x Meal Frequency Heatmap"
        ),
        use_container_width=True
    )

    st.markdown("""
**3.7. Plan Price Distribution**  
Whisker plot of price per plan type for outliers & range.
    """)
    st.plotly_chart(
        px.box(
            filtered,
            x='Plan_Type',
            y='Total_Price',
            title="Plan Price by Type",
            labels={'Plan_Type': 'Plan Type', 'Total_Price': 'Plan Price (INR)'}
        ),
        use_container_width=True
    )

# ==== 4. Raw Data Tab ====
with tabs[3]:
    st.title("🗂️ Raw Customer Data Explorer")
    st.markdown("""
Use filters to see exact data or download below.
    """)
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "Download Filtered Data",
        data=filtered.to_csv(index=False),
        file_name="Filtered_Customers.csv",
        mime="text/csv"
    )

st.sidebar.markdown("---")
st.sidebar.info(
    "Data and dashboard are for internal analytics and strategy planning only. For questions or custom views, contact the Data Team."
)
