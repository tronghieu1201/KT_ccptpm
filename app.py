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
        f"DRIVER={{ODBC Driver 17 for SQL Server}} প্রশিক্ষক;"
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

class ProductRepository:
    def get_all_products(self):
        products = []
        conn = None
        cursor = None
        try:
            conn = db_connect('ProductDB')
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Price, Image FROM Products")
            for row in cursor.fetchall():
                products.append(Product(row[0], row[1], row[2], row[3]))
        except Exception as e:
            print(f"Error getting all products: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return products

    def get_product_by_id(self, product_id):
        product = None
        conn = None
        cursor = None
        try:
            conn = db_connect('ProductDB')
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Price, Image FROM Products WHERE Id = ?", product_id)
            row = cursor.fetchone()
            if row:
                product = Product(row[0], row[1], row[2], row[3])
        except Exception as e:
            print(f"Error getting product by id {product_id}: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return product

    def add_product(self, product):
        conn = None
        cursor = None
        try:
            conn = db_connect('ProductDB')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Products (Name, Price, Image) VALUES (?, ?, ?)",
                           product.name, product.price, product.image)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_product(self, product):
        conn = None
        cursor = None
        try:
            conn = db_connect('ProductDB')
            cursor = conn.cursor()
            cursor.execute("UPDATE Products SET Name = ?, Price = ?, Image = ? WHERE Id = ?",
                           product.name, product.price, product.image, product.id)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating product: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_product(self, product_id):
        conn = None
        cursor = None
        try:
            conn = db_connect('ProductDB')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Products WHERE Id = ?", product_id)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


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