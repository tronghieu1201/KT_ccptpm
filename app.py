import pyodbc
import os
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Cấu hình kết nối SQL Server
DB_CONFIG = {
    'server': 'DESKTOP-B4U5OFT\SQLEXPRESS',
    'database': 'master', # Kết nối tới master để tạo KT_j2ee nếu chưa có
    'username': 'tronghieu',
    'password': '123456'
}

def db_connect(db_name=None):
    # If no db_name is provided, default to 'KT_j2ee' for CRUD operations
    current_db = DB_CONFIG['database'] # Store current db name
    if db_name:
        DB_CONFIG['database'] = db_name
    else:
        DB_CONFIG['database'] = 'KT_j2ee'
    
    # Use raw string for server name to handle backslashes correctly
    server_name = r"{}".format(DB_CONFIG['server'])

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};
        f"SERVER={server_name};
        f"DATABASE={DB_CONFIG['database']};
        f"UID={DB_CONFIG['username']};
        f"PWD={DB_CONFIG['password']}"
    )
    conn = None
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        print(f"Successfully connected to database: {DB_CONFIG['database']}") # DEBUG
    except Exception as e:
        print(f"Error connecting to database {DB_CONFIG['database']}: {e}") # DEBUG
        # Optionally, re-raise the exception or handle it more gracefully
    finally:
        DB_CONFIG['database'] = current_db # Restore original for consistency
    return conn

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
            conn = db_connect('KT_j2ee') # Use KT_j2ee
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
            conn = db_connect('KT_j2ee') # Use KT_j2ee
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
            conn = db_connect('KT_j2ee') # Use KT_j2ee
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
            conn = db_connect('KT_j2ee') # Use KT_j2ee
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
            conn = db_connect('KT_j2ee') # Use KT_j2ee
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
    print("Attempting to initialize database...") # DEBUG
    try:
        # Connect to master to check/create KT_j2ee
        conn = db_connect('master')
        cursor = conn.cursor()

        # Check if KT_j2ee exists, create if not
        cursor.execute(f"IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = N'KT_j2ee') CREATE DATABASE KT_j2ee;")
        print("KT_j2ee checked/created.")
        cursor.close()
        conn.close()

        # Connect to KT_j2ee to create Products table
        conn = db_connect('KT_j2ee') # Use KT_j2ee
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

product_repo = ProductRepository()

@app.route('/products')
def list_products():
    products = product_repo.get_all_products()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image_file = request.files['image']
        image_filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename
        
        new_product = Product(None, name, price, image_filename)
        if product_repo.add_product(new_product):
            flash('Product added successfully!', 'success')
        else:
            flash('Error adding product.', 'error')
        return redirect(url_for('list_products'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = product_repo.get_product_by_id(product_id)
    if not product:
        return "Product not found", 404

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        
        image_file = request.files['image']
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = filename
        elif 'image' not in request.files: # if no new image is uploaded, retain old image
            pass # product.image already holds the old image filename

        product_repo.update_product(product)
        return redirect(url_for('list_products'))
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product_repo.delete_product(product_id)
    return redirect(url_for('list_products'))

if __name__ == '__main__':
    init_db() # Initialize database before running the app
    print("Flask app about to run...") # DEBUG
    app.run(debug=True)