from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Jwitness1316@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

@app.cli.command('setup_db')
def setup_db():
    db.create_all()
    print("Database setup complete.")


# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)

    orders = db.relationship('Order', backref='user', lazy=True)

    def __init__(self, name, address, email):
        self.name = name
        self.address = address
        self.email = email


# Product Model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, product_name, price):
        self.product_name = product_name
        self.price = price


# Order Model
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    products = db.relationship('Product', secondary='order_product', lazy='subquery', backref=db.backref('orders', lazy=True))

    def __init__(self, user_id, order_date):
        self.user_id = user_id
        self.order_date = order_date


# Order_Product Association Table (Many-to-Many relationship)
order_product = db.Table('order_product',
                         db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
                         db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
                         )


# User Schema (for Serialization and Validation)
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True


# Product Schema (for Serialization and Validation)
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True


# Order Schema (for Serialization and Validation)
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True


# User Endpoints

# GET /users: Retrieve all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)
    return user_schema.jsonify(users)


# GET /users/<id>: Retrieve a user by ID
@app.route('/users/<id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    user_schema = UserSchema()
    return user_schema.jsonify(user)


# POST /users: Create a new user
@app.route('/users', methods=['POST'])
def create_user():
    user_data = request.get_json()
    user_schema = UserSchema()
    try:
        user = user_schema.load(user_data)
        db.session.add(user)
        db.session.commit()
        return user_schema.jsonify(user), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Email already exists'}), 400
    except ValidationError as err:
        return jsonify(err.messages), 400


# PUT /users/<id>: Update a user by ID
@app.route('/users/<id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    user_data = request.get_json()
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']
    
    db.session.commit()
    user_schema = UserSchema()
    return user_schema.jsonify(user)


# DELETE /users/<id>: Delete a user by ID
@app.route('/users/<id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200


# Product Endpoints

# GET /products: Retrieve all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_schema = ProductSchema(many=True)
    return product_schema.jsonify(products)


# GET /products/<id>: Retrieve a product by ID
@app.route('/products/<id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({'message': 'Product not found'}), 404
    product_schema = ProductSchema()
    return product_schema.jsonify(product)


# POST /products: Create a new product
@app.route('/products', methods=['POST'])
def create_product():
    product_data = request.get_json()
    product_schema = ProductSchema()
    product = product_schema.load(product_data)
    db.session.add(product)
    db.session.commit()
    return product_schema.jsonify(product), 201


# PUT /products/<id>: Update a product by ID
@app.route('/products/<id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({'message': 'Product not found'}), 404

    product_data = request.get_json()
    product.product_name = product_data['product_name']
    product.price = product_data['price']
    
    db.session.commit()
    product_schema = ProductSchema()
    return product_schema.jsonify(product)


# DELETE /products/<id>: Delete a product by ID
@app.route('/products/<id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({'message': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'}), 200


# Order Endpoints

# POST /orders: Create a new order
@app.route('/orders', methods=['POST'])
def create_order():
    order_data = request.get_json()
    order_schema = OrderSchema()
    order = order_schema.load(order_data)
    db.session.add(order)
    db.session.commit()
    return order_schema.jsonify(order), 201


# GET /orders/<order_id>/add_product/<product_id>: Add a product to an order
@app.route('/orders/<order_id>/add_product/<product_id>', methods=['GET'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get(order_id)
    product = Product.query.get(product_id)
    if order is None or product is None:
        return jsonify({'message': 'Order or Product not found'}), 404

    # Prevent duplicate entries
    if product in order.products:
        return jsonify({'message': 'Product already in order'}), 400

    order.products.append(product)
    db.session.commit()
    order_schema = OrderSchema()
    return order_schema.jsonify(order)


# DELETE /orders/<order_id>/remove_product: Remove a product from an order
@app.route('/orders/<order_id>/remove_product', methods=['DELETE'])
def remove_product_from_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({'message': 'Order not found'}), 404

    product_id = request.get_json()['product_id']
    product = Product.query.get(product_id)
    if product not in order.products:
        return jsonify({'message': 'Product not found in order'}), 404

    order.products.remove(product)
    db.session.commit()
    order_schema = OrderSchema()
    return order_schema.jsonify(order)


# GET /orders/user/<user_id>: Get all orders for a user
@app.route('/orders/user/<user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    if not orders:
        return jsonify({'message': 'No orders found for this user'}), 404
    order_schema = OrderSchema(many=True)
    return order_schema.jsonify(orders)


# GET /orders/<order_id>/products: Get all products for an order
@app.route('/orders/<order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({'message': 'Order not found'}), 404
    product_schema = ProductSchema(many=True)
    return product_schema.jsonify(order.products)


# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
