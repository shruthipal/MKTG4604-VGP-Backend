# Data Dictionary

## 1. Retailer Inventory Dataset (`inventory_data.csv`)

| Column Name | Data Type | Description | Example |
|---|---|---|---|
| retailer_id | String | Unique identifier for each retailer | R1 |
| retailer_name | String | Name of the retailer | FreshMart |
| retailer_type | String | Type of retailer business | Grocery |
| location | String | City and state of the retailer | Boston MA |
| product_name | String | Name of the inventory item | Milk |
| category | String | General product category | Dairy |
| perishability | String | Shelf-life classification of the product | Perishable |
| inventory_level | Integer | Current quantity of the product in stock | 120 |
| optimal_inventory | Integer | Target or ideal inventory level for the product | 80 |
| expiration_date | Date / Blank | Date the product expires, blank for non-expiring items like clothing | 2026-04-15 |
| demand_score | Integer | Relative demand level for the item on a scale from 1–100 | 42 |

### Notes
- `perishability` values may include: `Perishable`, `Semi-Perishable`, `Non-Perishable`
- `expiration_date` is blank for clothing and other non-expiring goods
- `inventory_level` and `optimal_inventory` can be compared to identify excess inventory
- `demand_score` is a relative score meant to simulate expected demand

---

## 2. Buyer / Recipient Requests Dataset (`buyer_requests.csv`)

| Column Name | Data Type | Description | Example |
|---|---|---|---|
| buyer_id | String | Unique identifier for each buyer or recipient | B1 |
| buyer_name | String | Name of the buyer, reseller, or nonprofit | Goodwill |
| buyer_type | String | Type of organization receiving goods | Resale Nonprofit |
| location | String | City and state of the buyer or recipient | Boston MA |
| requested_products | String | One or more requested products separated by `|` | T-Shirts\|Jeans\|Hoodies |
| category_preferences | String | Preferred product category for the request | Apparel |
| accepted_perishability | String | Type of perishability the buyer can accept | Non-Perishable |
| quantity_needed | Integer | Preferred number of units requested | 80 |
| max_quantity | Integer | Maximum number of units the buyer can accept | 200 |
| needed_by_date | Date | Latest useful date for receiving the products | 2026-05-15 |
| purchase_model | String | Whether goods are accepted as donation or discounted purchase | Donation |
| max_price_ratio | Decimal | Maximum share of retail price the buyer will pay | 0.00 |
| urgency_level | String | Relative urgency of the request | High |
| storage_capacity | String | Amount of storage the buyer has available | High |
| notes | String | Extra context about the request | Looking for gently used everyday clothing for resale |

### Notes
- `requested_products` may contain multiple items in one field using `|` as a separator
- `purchase_model` values may include: `Donation`, `Discounted Purchase`
- `max_price_ratio` uses retail price as the reference point:
  - `0.00` = donation only
  - `0.35` = buyer can pay up to 35% of retail price
- `accepted_perishability` helps match buyers with suitable inventory timing
- `needed_by_date` is important for matching against expiration-sensitive inventory
- `notes` provides extra context that can be useful for LLM retrieval or semantic matching

---

## 3. Matching Logic Relevance

These two datasets are designed to support future retailer-to-buyer matching.

### Key matching fields
- `product_name` ↔ `requested_products`
- `category` ↔ `category_preferences`
- `perishability` ↔ `accepted_perishability`
- `inventory_level` / `optimal_inventory` ↔ `quantity_needed` / `max_quantity`
- `expiration_date` ↔ `needed_by_date`
- `unit pricing logic` ↔ `purchase_model` / `max_price_ratio`
- `location` ↔ `location`

### Intended use
These fields can support:
- rule-based matching
- similarity scoring
- vector database retrieval
- LLM-generated recommendations for donation or discounted resale
