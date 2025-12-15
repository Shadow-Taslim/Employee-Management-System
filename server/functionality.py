#functionality queries

import mysql.connector

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="aakriti",
  database="employee"
)

mycursor = mydb.cursor(buffered=True)

