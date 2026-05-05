# ETL Pipeline — Solution Description

## Stack

pandas handles the cleaning because the datasets are small and it gives direct, readable control over every transformation. PySpark covers the optional requirement — same logic but in a distributed framework that scales when data outgrows a single machine. DuckDB serves as the local warehouse because it needs zero setup and runs from a single file. pytest verifies that every cleaning rule does what it is supposed to.

## What was cleaned and why

Rows with no primary key were dropped across all four tables — without an ID there is nothing to join on. Duplicate primary keys were deduplicated keeping the first occurrence since a repeated key breaks any downstream aggregation.

In customers, invalid emails were set to null rather than dropping the whole row, and an is_email_valid flag was added so analysts can filter later. Unparseable timestamps became null for the same reason — the row is still useful without a date. In products, rows with a price of zero or below were dropped entirely because a non-positive price silently corrupts any revenue calculation. In orders, mixed-case statuses like "COMPLETED" were normalised to lowercase, and rows with unknown statuses were dropped. Orders pointing to customers that no longer exist after cleaning were also removed to preserve referential integrity. The same logic was applied to order_items, dropping any row whose order_id or product_id had no match in the clean tables, along with rows where quantity was zero or negative.

## Output tables

The pipeline writes four clean staging tables and five analytical mart tables into DuckDB. mart_revenue_by_product and mart_revenue_by_customer show where revenue comes from at product and customer level. mart_monthly_sales tracks completed-order revenue over time. mart_order_status_summary gives an operational view of order states. mart_category_performance rolls up sales by product category.

## Running it

Drop new CSVs into data/raw, open the notebook, and run all cells. The first cell installs all dependencies automatically so a clean environment is ready in under ten minutes.
