import json
import mysql.connector

# Database connection parameters
config = {
    "user": "root",
    "password": "",
    "host": "localhost",
    "database": "iot",
    "raise_on_warnings": True
}

# Establish a database connection
conn = mysql.connector.connect(**config)

# Create a cursor object
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM lamp")

# Fetch all rows from the last executed query
rows = cursor.fetchall()

# parse json data on column 3
for row in rows:
    json_data = json.loads(row[3])  # Parse the JSON string from the third column
    print(json_data[0])
    

# Close the cursor and connection
cursor.close()
conn.close()