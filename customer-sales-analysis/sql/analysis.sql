-- Customer Sales Analysis (MySQL 8+)
-- Import data/sales.csv into this table before running the analysis queries.

CREATE TABLE IF NOT EXISTS sales (
    order_id VARCHAR(12) PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id VARCHAR(12) NOT NULL,
    segment VARCHAR(30) NOT NULL,
    city VARCHAR(40) NOT NULL,
    category VARCHAR(40) NOT NULL,
    product VARCHAR(80) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2) NOT NULL,
    revenue DECIMAL(12,2) NOT NULL,
    cost DECIMAL(12,2) NOT NULL,
    profit DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    customer_rating DECIMAL(2,1) NOT NULL,
    CHECK (quantity > 0),
    CHECK (discount_pct BETWEEN 0 AND 100)
);

-- 1. Executive KPIs
SELECT
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(100 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS profit_margin_pct,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS average_order_value,
    ROUND(AVG(customer_rating), 2) AS average_rating
FROM sales;

-- 2. Monthly trend
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit
FROM sales
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;

-- 3. Category performance
SELECT
    category,
    SUM(quantity) AS units,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS margin_pct
FROM sales
GROUP BY category
ORDER BY revenue DESC;

-- 4. City performance and revenue share
WITH city_sales AS (
    SELECT city, SUM(revenue) AS revenue, SUM(profit) AS profit
    FROM sales
    GROUP BY city
)
SELECT
    city,
    ROUND(revenue, 2) AS revenue,
    ROUND(profit, 2) AS profit,
    ROUND(100 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct
FROM city_sales
ORDER BY revenue DESC;

-- 5. Top five products
SELECT
    product,
    COUNT(DISTINCT order_id) AS orders,
    SUM(quantity) AS units,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit
FROM sales
GROUP BY product
ORDER BY revenue DESC
LIMIT 5;

-- 6. Segment comparison
SELECT
    segment,
    COUNT(DISTINCT customer_id) AS customers,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS average_order_value
FROM sales
GROUP BY segment
ORDER BY revenue DESC;

-- 7. Discount-band profitability
SELECT
    CASE
        WHEN discount_pct = 0 THEN 'No discount'
        WHEN discount_pct <= 10 THEN '1-10%'
        ELSE '11-20%'
    END AS discount_band,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS margin_pct
FROM sales
GROUP BY discount_band
ORDER BY MIN(discount_pct);

-- 8. Repeat customers
SELECT
    customer_id,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS lifetime_revenue
FROM sales
GROUP BY customer_id
HAVING COUNT(DISTINCT order_id) > 1
ORDER BY lifetime_revenue DESC, orders DESC;

-- 9. Rank products inside each category
WITH product_sales AS (
    SELECT category, product, SUM(revenue) AS revenue
    FROM sales
    GROUP BY category, product
)
SELECT
    category,
    product,
    ROUND(revenue, 2) AS revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS category_rank
FROM product_sales
ORDER BY category, category_rank;

-- 10. Data-quality checks (all values should be zero)
SELECT
    SUM(order_id IS NULL) AS missing_order_ids,
    COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_order_ids,
    SUM(quantity <= 0) AS invalid_quantities,
    SUM(discount_pct NOT BETWEEN 0 AND 100) AS invalid_discounts,
    SUM(ABS(revenue - quantity * unit_price * (1 - discount_pct / 100)) > 0.01)
        AS invalid_revenue_rows,
    SUM(ABS(profit - (revenue - cost)) > 0.01) AS invalid_profit_rows
FROM sales;
