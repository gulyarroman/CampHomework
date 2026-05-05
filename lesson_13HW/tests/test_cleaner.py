
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

EMAIL_RE = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
VALID_STATUSES = {"pending", "completed", "cancelled", "returned", "shipped"}

def clean_customers(df):
    df = df.copy()
    df = df.dropna(subset=["customer_id"])
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    df["customer_id"] = df["customer_id"].astype(int)
    df["is_email_valid"] = df["email"].str.match(EMAIL_RE, na=False)
    df.loc[~df["is_email_valid"], "email"] = np.nan
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df.reset_index(drop=True)

def clean_products(df):
    df = df.copy()
    df = df.dropna(subset=["product_id"])
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    df = df[df["price"] > 0]
    df["product_id"] = df["product_id"].astype(int)
    return df.reset_index(drop=True)

def clean_orders(df, valid_customers):
    df = df.copy()
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    df["order_status"] = df["order_status"].str.lower().str.strip()
    df = df[df["order_status"].isin(VALID_STATUSES)]
    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = df["customer_id"].astype(int)
    df = df[df["customer_id"].isin(valid_customers["customer_id"])]
    return df.reset_index(drop=True)

def clean_order_items(df, valid_orders, valid_products):
    df = df.copy()
    df = df.drop_duplicates(subset=["order_item_id"], keep="first")
    df = df[df["quantity"] > 0]
    df["order_id"]   = df["order_id"].astype(int)
    df["product_id"] = df["product_id"].astype(int)
    df = df[df["order_id"].isin(valid_orders["order_id"])]
    df = df[df["product_id"].isin(valid_products["product_id"])]
    return df.reset_index(drop=True)

# --- tests ---

def test_customers_drops_null_id():
    df = pd.DataFrame({"customer_id":[None,1],"email":["a@b.com","a@b.com"],
                       "country":["DE","DE"],"created_at":["2024-01-01","2024-01-01"]})
    assert len(clean_customers(df)) == 1

def test_customers_removes_duplicates():
    df = pd.DataFrame({"customer_id":[1,1],"email":["a@b.com","c@d.com"],
                       "country":["DE","PL"],"created_at":["2024-01-01","2024-01-02"]})
    assert len(clean_customers(df)) == 1

def test_customers_nulls_invalid_email():
    df = pd.DataFrame({"customer_id":[1,2],"email":["bad-email","good@ok.com"],
                       "country":["DE","DE"],"created_at":["2024-01-01","2024-01-01"]})
    result = clean_customers(df)
    assert pd.isna(result.loc[result.customer_id==1,"email"].iloc[0])
    assert result.loc[result.customer_id==2,"email"].iloc[0] == "good@ok.com"

def test_products_drops_nonpositive_price():
    df = pd.DataFrame({"product_id":[1,2,3],"name":["A","B","C"],
                       "category":["X","X","X"],"price":[100,-5,0]})
    assert len(clean_products(df)) == 1

def test_orders_normalises_status():
    cust = pd.DataFrame({"customer_id":[1]})
    df = pd.DataFrame({"order_id":[1],"customer_id":[1],
                       "order_status":["COMPLETED"],"created_at":["2024-01-01"]})
    result = clean_orders(df, cust)
    assert result["order_status"].iloc[0] == "completed"

def test_orders_drops_unknown_status():
    cust = pd.DataFrame({"customer_id":[1]})
    df = pd.DataFrame({"order_id":[1,2],"customer_id":[1,1],
                       "order_status":["completed","mystery"],"created_at":["2024-01-01","2024-01-01"]})
    assert len(clean_orders(df, cust)) == 1

def test_orders_drops_missing_customer():
    cust = pd.DataFrame({"customer_id":[1]})
    df = pd.DataFrame({"order_id":[1,2],"customer_id":[1,999],
                       "order_status":["completed","completed"],"created_at":["2024-01-01","2024-01-01"]})
    assert len(clean_orders(df, cust)) == 1

def test_order_items_drops_nonpositive_qty():
    orders   = pd.DataFrame({"order_id":[1]})
    products = pd.DataFrame({"product_id":[10]})
    df = pd.DataFrame({"order_item_id":[1,2,3],"order_id":[1,1,1],
                       "product_id":[10,10,10],"quantity":[3,0,-1]})
    assert len(clean_order_items(df, orders, products)) == 1

def test_order_items_drops_orphan_order():
    orders   = pd.DataFrame({"order_id":[1]})
    products = pd.DataFrame({"product_id":[10]})
    df = pd.DataFrame({"order_item_id":[1,2],"order_id":[1,999],
                       "product_id":[10,10],"quantity":[1,1]})
    assert len(clean_order_items(df, orders, products)) == 1
