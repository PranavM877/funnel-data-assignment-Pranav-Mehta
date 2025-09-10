# funnel-data-assignment-Pranav-Mehta


## Quickstart

1. Install dependencies:
  all the requirements are mentioned in requirements.txt

2. Run the report generation:
    ```bash
    python evo_report.py --events events.csv --messages messages.csv --orders orders.csv --out ./out/
    ```
## Data Setup
these are required changes in dataset before doing any work the name of database on mysql workbench i used was company_db.
Use the provided `data_setup.sql` to prepare the database:
```sql
USE company_db;

SET SQL_SAFE_UPDATES = 0;

UPDATE orders
SET canceled_at = NULL
WHERE canceled_at = '';

select * from events;
select * from inventory;
select * from messages;
select * from orders;
select * from products;
