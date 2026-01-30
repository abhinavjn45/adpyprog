import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Silver Price Calculator & Silver Sales Analysis",
    page_icon="💰",
    layout="wide",
)

st.title("Silver Price Calculator & Silver Sales Analysis")
st.write("This is a simple Streamlit application for calculating silver prices and analyzing silver sales.")

# Silver Price Calculator
st.header("1. Silver Price Calculator")

col1, col2, col3 = st.columns(3)
with col1:
    weight = st.number_input("Enter weight of silver", min_value=0.0, value=100.0, step=1.0)
    unit = st.selectbox("Select unit", ["grams", "kilograms"])
with col2:
    price_per_gram = st.number_input("Current price per gram (INR)", min_value=0.0, value=80.0, step=0.1)
with col3:
    currency = st.selectbox("Currency", ["INR", "USD"])
    conversion_rate = st.number_input("INR to USD rate", min_value=0.0, value=0.012, step=0.001, help="Current conversion rate (1 INR = ? USD)")

# Convert weight to grams if needed
if unit == "kilograms":
    weight_grams = weight * 1000
else:
    weight_grams = weight

total_cost_inr = weight_grams * price_per_gram

if currency == "INR":
    st.success(f"Total Cost: ₹{total_cost_inr:,.2f} INR")
else:
    total_cost_usd = total_cost_inr * conversion_rate
    st.success(f"Total Cost: ${total_cost_usd:,.2f} USD (at {conversion_rate} USD/INR)")


# Historical Silver Price Chart
st.header("2. Historical Silver Price Chart")
hist_df = pd.read_csv("historical_silver_price.csv")

filter_option = st.radio(
    "Filter by price per kg:",
    ("≤ 20,000 INR", "20,000 - 30,000 INR", "≥ 30,000 INR")
)

if filter_option == "≤ 20,000 INR":
    filtered = hist_df[hist_df["Silver_Price_INR_per_kg"] <= 20000]
elif filter_option == "20,000 - 30,000 INR":
    filtered = hist_df[(hist_df["Silver_Price_INR_per_kg"] > 20000) & (hist_df["Silver_Price_INR_per_kg"] < 30000)]
else:
    filtered = hist_df[hist_df["Silver_Price_INR_per_kg"] >= 30000]

filtered["Date"] = filtered["Year"].astype(str) + "-" + filtered["Month"]

fig = px.line(
    filtered,
    x="Date",
    y="Silver_Price_INR_per_kg",
    title="Historical Silver Price (INR per kg)",
    labels={"Silver_Price_INR_per_kg": "INR per kg", "Date": "Date"}
)
fig.update_xaxes(tickangle=45, tickmode='array', tickvals=filtered["Date"][::max(1, len(filtered)//12)])
st.plotly_chart(fig, use_container_width=True)


# Silver Sales Dashboard
st.header("3. Silver Sales Dashboard")
sales_df = pd.read_csv("state_wise_silver_purchased_kg.csv")


# --- India State-wise Map Visualization using .shp file ---
try:
    state_gdf = gpd.read_file("map_files/State/State.shp")
    # Try to join with sales_df for future coloring (if possible)
    # Attempt to find the column with state names (must be string/object type)
    state_name_col = None
    for col in state_gdf.columns:
        if (('state' in col.lower() or 'st_nm' in col.lower() or 'name' in col.lower())
            and state_gdf[col].dtype == object):
            state_name_col = col
            break
    if state_name_col:
        # Clean up state names for better matching
        state_gdf[state_name_col] = state_gdf[state_name_col].str.strip().str.title()
        sales_df['State'] = sales_df['State'].str.strip().str.title()
        merged_gdf = state_gdf.merge(sales_df, left_on=state_name_col, right_on='State', how='left')
        fig_map = px.choropleth(
            merged_gdf,
            geojson=merged_gdf.geometry.__geo_interface__,
            locations=merged_gdf.index,
            color="Silver_Purchased_kg",
            hover_name=state_name_col,
            color_continuous_scale="Blues",
            labels={"Silver_Purchased_kg": "Silver Purchased (kg)"},
            title="State-wise Silver Purchases (kg)"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Could not find a string state name column in the shapefile for joining. Showing outlines only.")
        state_gdf = state_gdf.to_crs(epsg=4326)
        fig_map = px.choropleth(
            state_gdf,
            geojson=state_gdf.geometry.__geo_interface__,
            locations=state_gdf.index,
            color_discrete_sequence=["#636EFA"],
            title="India States Map (Outline Only)"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load State shapefile: {e}")

# Top 5 States Bar Chart
st.subheader("Top 5 States by Silver Purchases")
top5 = sales_df.sort_values("Silver_Purchased_kg", ascending=False).head(5)
fig_bar = px.bar(
    top5,
    x="State",
    y="Silver_Purchased_kg",
    color="Silver_Purchased_kg",
    color_continuous_scale="Blues",
    labels={"Silver_Purchased_kg": "Silver Purchased (kg)"}
)

st.plotly_chart(fig_bar, use_container_width=True)

# January Monthly Silver Price Trend
st.subheader("January Silver Price Trend")
january_df = hist_df[hist_df['Month'].str.lower() == 'jan'].copy()

fig_jan = px.line(
    january_df,
    x='Year',
    y='Silver_Price_INR_per_kg',
    title='INR per kg',
    labels={'Silver_Price_INR_per_kg': 'INR per kg', 'Year': 'Year'}
)
fig_jan.update_xaxes(type='category')
st.plotly_chart(fig_jan, use_container_width=True)