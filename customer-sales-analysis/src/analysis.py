from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "sales.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

REQUIRED_COLUMNS = {
    "order_id", "order_date", "customer_id", "segment", "city", "category",
    "product", "quantity", "unit_price", "discount_pct", "revenue", "cost",
    "profit", "payment_method", "customer_rating",
}


def load_and_validate(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="raise")
    numeric = [
        "quantity", "unit_price", "discount_pct", "revenue",
        "cost", "profit", "customer_rating",
    ]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="raise")
    df = df.drop_duplicates(subset="order_id", keep="first").copy()

    if df["order_id"].isna().any() or df["order_id"].duplicated().any():
        raise ValueError("order_id must be present and unique")
    if (df["quantity"] <= 0).any():
        raise ValueError("quantity must be positive")
    if (~df["discount_pct"].between(0, 100)).any():
        raise ValueError("discount_pct must be between 0 and 100")

    expected_revenue = (
        df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    ).round(2)
    if not expected_revenue.equals(df["revenue"].round(2)):
        raise ValueError("Revenue does not match quantity, price, and discount")

    expected_profit = (df["revenue"] - df["cost"]).round(2)
    if not expected_profit.equals(df["profit"].round(2)):
        raise ValueError("Profit does not match revenue minus cost")

    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    return df


def create_summary(df: pd.DataFrame) -> pd.DataFrame:
    revenue = df["revenue"].sum()
    profit = df["profit"].sum()
    orders = df["order_id"].nunique()
    return pd.DataFrame({
        "kpi": [
            "orders", "revenue", "profit", "profit_margin_pct",
            "average_order_value", "average_customer_rating",
        ],
        "value": [
            orders,
            round(revenue, 2),
            round(profit, 2),
            round(profit / revenue * 100, 2),
            round(revenue / orders, 2),
            round(df["customer_rating"].mean(), 2),
        ],
    })


def grouped_performance(df: pd.DataFrame, column: str) -> pd.DataFrame:
    result = (
        df.groupby(column, as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
        )
    )
    result["profit_margin_pct"] = (result["profit"] / result["revenue"] * 100).round(2)
    return result.sort_values("revenue", ascending=False)


def save_bar(data: pd.DataFrame, label: str, title: str, filename: str) -> None:
    ordered = data.sort_values("revenue")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(ordered[label], ordered["revenue"], color="#22b89a")
    ax.set_title(title)
    ax.set_xlabel("Revenue (INR)")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=160)
    plt.close(fig)


def run_analysis() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = load_and_validate()

    summary = create_summary(df)
    category = grouped_performance(df, "category")
    city = grouped_performance(df, "city")
    monthly = grouped_performance(df, "month").sort_values("month")

    summary.to_csv(OUTPUT_DIR / "kpi_summary.csv", index=False)
    category.to_csv(OUTPUT_DIR / "category_performance.csv", index=False)
    city.to_csv(OUTPUT_DIR / "city_performance.csv", index=False)
    monthly.to_csv(OUTPUT_DIR / "monthly_performance.csv", index=False)

    save_bar(category, "category", "Revenue by Category", "revenue_by_category.png")
    save_bar(city, "city", "Revenue by City", "revenue_by_city.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly["month"], monthly["revenue"], marker="o", color="#2563eb")
    ax.set_title("Monthly Revenue Trend")
    ax.set_ylabel("Revenue (INR)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "monthly_revenue.png", dpi=160)
    plt.close(fig)

    print(summary.to_string(index=False))
    print(f"\nAnalysis complete. Results saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_analysis()
