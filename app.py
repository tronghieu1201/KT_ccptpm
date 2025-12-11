import pyodbc
from flask import Flask, render_template

app = Flask(__name__)

# Cấu hình kết nối SQL Server
DB_CONFIG = {
    'server': 'DESKTOP-B4U5OFT\\SQLEXPRESS',
    'database': 'master', # Kết nối tới master để tạo ProductDB nếu chưa có
    'username': 'tronghieu',
    'password': '123456'
}

def db_connect(db_name=None):
    if db_name:
        DB_CONFIG['database'] = db_name
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return pyodbc.connect(conn_str, autocommit=True)

class Product:
    def __init__(self, id, name, price, image):
        self.id = id
        self.name = name
        self.price = price
        self.image = image

def init_db():
    conn = None
    cursor = None
    try:
        # Connect to master to check/create ProductDB
        conn = db_connect('master')
        cursor = conn.cursor()

        # Check if ProductDB exists, create if not
        cursor.execute(f"IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = N'ProductDB') CREATE DATABASE ProductDB;")
        print("ProductDB checked/created.")
        cursor.close()
        conn.close()

        # Connect to ProductDB to create Products table
        conn = db_connect('ProductDB')
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Products')
            CREATE TABLE Products (
                Id INT PRIMARY KEY IDENTITY(1,1),
                Name NVARCHAR(255) NOT NULL,
                Price DECIMAL(10, 2) NOT NULL,
                Image NVARCHAR(255)
            );
        """)
        print("Products table checked/created.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db() # Initialize database before running the app
    app.run(debug=True)
