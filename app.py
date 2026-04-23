from fastapi import FastAPI, Request
from pydantic import BaseModel
import pandas as pd
from typing import Optional, Union
from datetime import datetime

app = FastAPI()

products = pd.read_csv("product_inventory.csv")
orders = pd.read_csv("orders.csv", dtype={"order_id": str})
orders["order_id"] = orders["order_id"].astype(str).str.strip()

products["is_sale"] = products["is_sale"].astype(str).str.upper() == "TRUE"
products["is_clearance"] = products["is_clearance"].astype(str).str.upper() == "TRUE"

with open("policy.txt", "r") as f:
    policy = f.read()

class OrderRequest(BaseModel):
    order_id: Union[str, int]

class ReturnRequest(BaseModel):
    order_id: Union[str, int]

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.post("/search_products")
def search_products(
    size: Optional[int] = None,
    max_price: Optional[float] = None,
    is_sale: Optional[bool] = None
):
    df = products.copy()

    if size is not None:
        df = df[df["sizes_available"].astype(str).apply(
            lambda x: str(size) in x.split("|")
        )]
        def has_stock(row):
            try:
                stock = eval(row["stock_per_size"])
                return stock.get(str(size), stock.get(size, 0)) > 0
            except:
                return True
        df = df[df.apply(has_stock, axis=1)]

    if max_price is not None:
        df = df[df["price"] <= max_price]

    if is_sale is not None:
        df = df[df["is_sale"] == is_sale]

    if max_price is not None:
        df["price_score"] = 1 - ((max_price - df["price"]) / max_price)
    else:
        df["price_score"] = 0

    df["bs_score"] = df["bestseller_score"] / 100
    df["sale_bonus"] = df["is_sale"].apply(lambda x: 0.2 if x else 0)
    df["final_score"] = (
        df["bs_score"] * 0.25 +
        df["price_score"] * 0.55 +
        df["sale_bonus"] * 0.20
    )
    df = df.sort_values("final_score", ascending=False)
    cols_to_drop = ["price_score", "bs_score", "sale_bonus", "final_score"]
    return {
        "results": df.drop(columns=cols_to_drop, errors="ignore")
                     .head(3).to_dict(orient="records")
    }

@app.post("/get_order")
def get_order(req: OrderRequest):
    order_id = str(req.order_id).strip()
    print("🔥 RECEIVED ORDER_ID:", order_id)
    order = orders[orders["order_id"] == order_id]
    if order.empty:
        return {"error": "Order not found"}
    return {"order": order.iloc[0].to_dict()}

@app.post("/evaluate_return")
def evaluate_return(req: ReturnRequest):
    order_id = str(req.order_id).strip()
    print("🔥 EVALUATE RETURN:", order_id)

    order = orders[orders["order_id"] == order_id]
    if order.empty:
        return {"eligible": False, "reason": "Order not found"}

    order = order.iloc[0]
    product = products[products["product_id"] == order["product_id"]]
    if product.empty:
        return {"eligible": False, "reason": "Product not found"}

    product = product.iloc[0]

    # Calculate days passed from order date
    order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
    days_passed = (datetime.now() - order_date).days
    print(f"📅 Order date: {order['order_date']} | Days passed: {days_passed}")

    # Clearance — final sale, no returns
    if product["is_clearance"]:
        return {"eligible": False, "reason": "Clearance items are final sale — cannot be returned or exchanged"}

    # Vendor exception: Aurelia Couture — exchange only
    if product["vendor"] == "Aurelia Couture":
        return {"eligible": True, "type": "exchange_only", "reason": "Aurelia Couture items can be exchanged only — no refunds"}

    # Vendor exception: Nocturne — extended 21-day window
    if product["vendor"] == "Nocturne":
        if days_passed <= 21:
            return {"eligible": True, "type": "refund", "reason": f"Nocturne extended 21-day return window applies. {days_passed} days have passed — eligible for refund"}
        return {"eligible": False, "reason": f"Nocturne return window exceeded — {days_passed} days passed, limit is 21 days"}

    # Sale items — 7-day store credit only
    if product["is_sale"]:
        if days_passed <= 7:
            return {"eligible": True, "type": "store_credit", "reason": f"Sale item — eligible for store credit only. {days_passed} days have passed, within the 7-day window"}
        return {"eligible": False, "reason": f"Sale item return window exceeded — {days_passed} days passed, limit is 7 days"}

    # Normal items — 14-day full refund
    if days_passed <= 14:
        return {"eligible": True, "type": "refund", "reason": f"Eligible for full refund. {days_passed} days have passed, within the 14-day return window"}

    return {"eligible": False, "reason": f"Return window exceeded — {days_passed} days have passed, limit is 14 days"}
