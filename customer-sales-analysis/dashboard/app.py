from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "sales.csv"

st.set_page_config(page_title="Customer Sales Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    data["month"] = data["order_date"].dt.to_period("M").astype(str)
    return data


def multiselect(label: str, values: pd.Series) -> list[str]:
    options = sorted(values.unique().tolist())
    return st.sidebar.multiselect(label, options, default=options)


df = load_data()
st.title("Customer Sales Dashboard")
st.caption("Interactive analysis of 180 synthetic retail transactions from 2025")

min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
date_range = st.sidebar.date_input(
    "Order date", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
cities = multiselect("City", df["city"])
categories = multiselect("Category", df["category"])
segments = multiselect("Segment", df["segment"])

if len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date = end_date = pd.Timestamp(date_range[0])

filtered = df[
    df["order_date"].between(start_date, end_date)
    & df["city"].isin(cities)
    & df["category"].isin(categories)
    & df["segment"].isin(segments)
].copy()

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

revenue = filtered["revenue"].sum()
profit = filtered["profit"].sum()
orders = filtered["order_id"].nunique()
margin = profit / revenue if revenue else 0
average_order = revenue / orders if orders else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Revenue", f"₹{revenue:,.0f}")
k2.metric("Profit", f"₹{profit:,.0f}")
k3.metric("Margin", f"{margin:.1%}")
k4.metric("Orders", f"{orders:,}")
k5.metric("Avg. order", f"₹{average_order:,.0f}")

monthly = filtered.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
category = filtered.groupby("category", as_index=False)[["revenue", "profit"]].sum()
city = filtered.groupby("city", as_index=False)[["revenue", "profit"]].sum()

left, right = st.columns(2)
left.plotly_chart(
    px.line(monthly, x="month", y="revenue", markers=True, title="Monthly Revenue"),
    use_container_width=True,
)
right.plotly_chart(
    px.bar(category.sort_values("revenue"), x="revenue", y="category",
           orientation="h", color="profit", title="Category Performance"),
    use_container_width=True,
)

left, right = st.columns(2)
left.plotly_chart(
    px.bar(city.sort_values("revenue"), x="revenue", y="city",
           orientation="h", title="Revenue by City"),
    use_container_width=True,
)
right.plotly_chart(
    px.scatter(filtered, x="discount_pct", y="profit", size="revenue",
               color="category", hover_data=["product", "city"],
               title="Discount vs Profit"),
    use_container_width=True,
)

st.subheader("Filtered transactions")
st.dataframe(filtered.sort_values("order_date", ascending=False), use_container_width=True)
st.download_button(
    "Download filtered CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    "filtered_sales.csv",
    "text/csv",
)
