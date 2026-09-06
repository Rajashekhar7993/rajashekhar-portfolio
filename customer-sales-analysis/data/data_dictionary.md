# Data dictionary

| Column | Type | Description |
|---|---|---|
| order_id | text | Unique order identifier |
| order_date | date | Transaction date in YYYY-MM-DD format |
| customer_id | text | Synthetic customer identifier |
| segment | text | Consumer, Corporate, or Home Office |
| city | text | Sales city |
| category | text | Product category |
| product | text | Product name |
| quantity | integer | Units sold |
| unit_price | decimal | Listed price per unit in INR |
| discount_pct | integer | Discount percentage from 0 to 20 |
| revenue | decimal | quantity × unit price after discount |
| cost | decimal | Total product cost |
| profit | decimal | revenue − cost |
| payment_method | text | Payment channel |
| customer_rating | decimal | Rating from 3.0 to 5.0 |

All customers and transactions are synthetic. No real personal data or credentials are present.
