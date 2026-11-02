import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="Blinkit Dashboard", layout="wide")

# ========== HEADER WITH LOGO ==========
#col1, col2 = st.columns([0.15, 0.85])
#with col1:
    #st.image("Design_Assets/Blinkit_Logo.png", width=70)
    


#with col2:
#    st.markdown(
#        "<h1 style='color:#F7C600; text-align:left center;'>Blinkit Data Analysis Dashboard</h1>",
#        unsafe_allow_html=True
#    )



st.markdown(
    "<h1 style='color:#F7C600; text-align:left center;'>Blinkit Data Analysis Dashboard</h1>",
    unsafe_allow_html=True
    )

st.markdown("---")

# ========== CLEANED DATASET OVERVIEW ==========
st.subheader("Cleaned Dataset Overview")

df = pd.read_csv("Dataset/Blinkit_Cleaned_Data.csv")

# Show first 10 rows & 10 columns
st.dataframe(df.head(10).iloc[:, :10])

# ========== KPI REQUIREMENTS ==========
st.subheader("📊 KPI Requirements")

total_sales = df['Sales'].sum()
avg_sales = df['Sales'].mean()
no_of_items_sold = df['Sales'].count()
avg_ratings = df['Rating'].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales", f"${total_sales:,.0f}")
kpi2.metric("Average Sales", f"${avg_sales:,.1f}")
kpi3.metric("Items Sold", f"{no_of_items_sold:,.0f}")
kpi4.metric("Average Rating", f"{avg_ratings:.1f}")

st.markdown("---")

# ========== ANALYSIS IN SQL AND VISUALIZATION IN PYTHON ==========
st.subheader("📈 Analysis in SQL and Visualization in Python")

# --- Total Sales by Fat Content ---
st.markdown("###  Total Sales by Fat Content")
fat_df = pd.read_csv("Result_csv/Total Sales by Fat Content.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(fat_df)
with col2:
    sales_by_fat = df.groupby('Item Fat Content')['Sales'].sum()
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        sales_by_fat,
        labels=sales_by_fat.index,
        autopct="%.0f%%",
        startangle=90,
        wedgeprops={'edgecolor': 'black', 'linewidth': 1}
    )
    ax.set_title("Sales by Fat Content")
    st.pyplot(fig)
    
    
st.markdown(
    "<div style='background-color:#ffeb3b; padding:8px; border-radius:6px;'>"
    "<span style='color:#000000; font-weight:bold; font-size:16px;'>"
    "<span style='color:#00a651;'>★</span> Key Insight: Sales of Low Fat items are higher than Regular ones — approximately 65% for Low Fat vs 35% for Regular."
    "</span></div>",
    unsafe_allow_html=True
)


# --- Total Sales by Item Type ---
st.markdown("### Total Sales by Item Type")
type_df = pd.read_csv("Result_csv/Total Sales by Item Type.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(type_df)
with col2:
    sales_by_type = df.groupby('Item Type')['Sales'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(sales_by_type.index, sales_by_type.values)
    plt.xticks(rotation=90, fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    
    
st.markdown(
    "<div style='background-color:#ffeb3b; padding:8px; border-radius:6px;'>"
    "<span style='color:#000000; font-weight:bold; font-size:16px;'>"
    "<span style='color:#00a651;'>★</span> Key Insight: Fruits and Vegetables exhibit the highest sales performance among all Item Types."
    "</span></div>",
    unsafe_allow_html=True
)


# --- Fat Content by Outlet for Total Sales ---
st.markdown("### Fat Content by Outlet for Total Sales")
fat_outlet_df = pd.read_csv("Result_csv/Fat Content by Outlet for Total Sales.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(fat_outlet_df)
with col2:
    grouped = df.groupby(['Outlet Location Type', 'Item Fat Content'])['Sales'].sum().unstack()
    grouped = grouped[['Regular', 'Low Fat']]
    fig, ax = plt.subplots(figsize=(6, 3))
    grouped.plot(kind='bar', ax=ax)
    plt.xticks(rotation=0)
    plt.tight_layout()
    st.pyplot(fig)

# --- Total Sales by Outlet Establishment Year ---
st.markdown("### Total Sales by Outlet Establishment Year")
establish_df = pd.read_csv("Result_csv/Total Sales by Outlet Establishment.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(establish_df)
with col2:
    sales_by_year = df.groupby('Outlet Establishment Year')['Sales'].sum().sort_index()
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(sales_by_year.index, sales_by_year.values, marker='o')
    ax.set_title("Total Sales by Outlet Establishment")
    plt.tight_layout()
    st.pyplot(fig)

# --- Sales by Outlet Size ---
st.markdown("### Sales by Outlet Size")
size_df = pd.read_csv("Result_csv/Sales by Outlet Size.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(size_df)
with col2:
    sales_by_size = df.groupby('Outlet Size')['Sales'].sum()
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        sales_by_size,
        labels=sales_by_size.index,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={'edgecolor': 'black', 'linewidth': 1}
    )
    plt.tight_layout()
    st.pyplot(fig)


st.markdown(
    "<div style='background-color:#ffeb3b; padding:8px; border-radius:6px;'>"
    "<span style='color:#000000; font-weight:bold; font-size:16px;'>"
    "<span style='color:#00a651;'>★</span> Key Insight: Outlets with Medium size demonstrate higher sales compared to both Small and High Outlets."
    "</span></div>",
    unsafe_allow_html=True
)


# --- Total Sales by Outlet Location Type ---
st.markdown("### Total Sales by Outlet Location Type")
location_df = pd.read_csv("Result_csv/Sales by Outlet Location.csv")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(location_df)
with col2:
    sales_by_location = df.groupby('Outlet Location Type')['Sales'].sum().reset_index()
    sales_by_location = sales_by_location.sort_values('Sales', ascending=False)
    fig, ax = plt.subplots(figsize=(6, 3))
    sns.barplot(x='Sales', y='Outlet Location Type', data=sales_by_location, ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    
    
st.markdown(
    "<div style='background-color:#ffeb3b; padding:8px; border-radius:6px;'>"
    "<span style='color:#000000; font-weight:bold; font-size:16px;'>"
    "<span style='color:#00a651;'>★</span> Key Insight: Tier 3 outlet locations exhibit the highest sales compared to Tier 1 and Tier 2 locations."
    "</span></div>",
    unsafe_allow_html=True
)


# --- Heatmap ---
st.markdown("### Average Sales Distribution Across Outlet Type & Item Type (Heatmap)")
blinkit_cmap = LinearSegmentedColormap.from_list("blinkit", ["#fff200", "#c6ff00", "#00a651"])
pivot = df.pivot_table(values='Sales', index='Item Type', columns='Outlet Type', aggfunc='mean')

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap=blinkit_cmap, ax=ax)
plt.tight_layout()
st.pyplot(fig)


    
st.markdown(
    "<div style='background-color:#ffeb3b; padding:8px; border-radius:6px;'>"
    "<span style='color:#000000; font-weight:bold; font-size:16px;'>"
    "<span style='color:#00a651;'>★</span> Key Insight: Among all item types and outlet types, Hard Drinks in Supermarket Type 2 outlet record the highest average sales."
    "</span></div>",
    unsafe_allow_html=True
)

# --- Power BI Dashboard ---
st.markdown("### 📊 Blinkit Power BI Dashboard")
st.image("Output_Screenshots/Blinkit_Dashboard.png", use_container_width=True, caption="Power BI Dashboard")



st.markdown(
    """
    ---
    **Developed by:** Ashutosh Sahoo  
    **GitHub Repository:** [Click Here 🔗](https://github.com/Ashuytosh/Blinkit_Data_Analysis)
    """
)


