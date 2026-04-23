# Retail AI Agent 🛍️

An intelligent voice-based retail assistant built with FastAPI and Retell AI that handles product recommendations and customer support for returns and order lookups.

## What It Does

The agent simulates two roles in one system:

- **Personal Shopper** — Recommends products based on size, budget, and sale preferences
- **Customer Support** — Handles order lookups and evaluates return eligibility based on policy rules

## Tech Stack

- **FastAPI** — Backend API server
- **Pandas** — Data processing for products and orders
- **Retell AI** — Voice agent and LLM orchestration
- **ngrok** — Exposes local server to the internet for Retell to call
- **Python 3.10+**


## Project Structure

retail-ai-agent/
├── app.py                  # FastAPI server with all tool endpoints
├── orders.csv              # Order data (order_id, product_id, date, size, price)
├── product_inventory.csv   # Product data (title, vendor, price, sizes, stock, tags)
├── policy.txt              # Return policy rules
├── requirements.txt        # Python dependencies
└── README.md


## Tools / Endpoints

| Endpoint | Method | Description |
|---|---|---|
| /search_products | POST | Filter products by size, max price, sale status |
| /get_order | POST | Fetch order details by order ID |
| /evaluate_return | POST | Check return eligibility based on policy |
| `/` | GET | Health check |

## How to Run Locally

### 1. Clone the repo

git clone https://github.com/shashidhargenna/Retell-ai-agent.git
cd Retell-ai-agent


### 2. Install dependencies

pip install -r requirements.txt


### 3. Start the server

uvicorn app:app --reload


Server runs at `http://localhost:8000`

### 4. Expose via ngrok (for Retell to connect)

ngrok http 8000

Copy the ngrok URL and use it as the base URL in your Retell function configs.

## Example API Calls

### Search Products

curl -X POST "http://localhost:8000/search_products" \
  -H "Content-Type: application/json" \
  -d '{"size": 6, "max_price": 300, "is_sale": true}'


### Get Order

curl -X POST "http://localhost:8000/get_order" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "1"}'


### Evaluate Return
``bash
curl -X POST "http://localhost:8000/evaluate_return" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "1"}'

## Return Policy Logic

| Item Type | Return Window | Refund Type |

| Normal item | 14 days | Full refund |
| Sale item | 7 days | Store credit only |
| Clearance item | Not eligible | Final sale |
| Aurelia Couture | Any time | Exchange only |
| Nocturne | 21 days | Full refund |

## Agent Behavior

- **Never hallucinates** — always calls tools before answering
- **Converts word numbers** — "order one" → order_id = "1"
- **Multi-constraint filtering** — handles size + price + sale in one query
- **Stock-aware** — only recommends products with stock for the requested size
- **Policy-aware** — applies vendor exceptions and sale rules correctly
