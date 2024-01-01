from flask import Flask, Blueprint, render_template, request, abort, jsonify
from database import *
from datetime import datetime
from backendjobs import workers
from flask_sse import sse
from flask_caching import Cache
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from functools import wraps
from flask import request
from sqlalchemy import or_

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user is None or current_user.role != role:
                return render_template('index.html')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.sqlite3'
app.config['CACHE_TYPE'] = "RedisCache"
app.config['CACHE_REDIS_HOST'] = "localhost"
app.config['CACHE_REDIS_PORT'] = 6379
app.config['BROKER_CONNECTION_RETRY_ON_STARTUP'] = True
app.config['CELERY_BROKER_URL'] = "redis://localhost:6379/1"
app.config['CELERY_RESULT_BACKEND'] = "redis://localhost:6379/2"
app.config['CELERY_TIMEZONE'] = "Asia/Kolkata"
app.config['REDIS_URL'] = "redis://localhost:6379"
db.init_app(app)
app.app_context().push()
with app.app_context():
    db.create_all()
exist_admin=User.query.filter_by(role='admin').first()
if not exist_admin:
    the_admin = User(email="sumit@gmail.com", name="Sumit Kumar", role="admin", password=generate_password_hash("password",method='scrypt'))
    db.session.add(the_admin)
    db.session.commit()

app.config["REDIS_URL"] = "redis://localhost:6379"
# Create celery   
celery = workers.celery

# Update with configuration
celery.conf.update(
    broker_url = app.config["CELERY_BROKER_URL"],
    result_backend = app.config["CELERY_RESULT_BACKEND"],
    timezone = app.config["CELERY_TIMEZONE"],
    broker_connection_retry_on_startup=app.config["BROKER_CONNECTION_RETRY_ON_STARTUP"]
)
celery.conf.timezone = 'Asia/Kolkata' 


celery.Task = workers.ContextTask
app.app_context().push()
cache=Cache(app)
app.app_context().push()

app.register_blueprint(sse, url_prefix='/stream')

#---------------------- All operational endpoints --------------#
main = Blueprint('main', __name__)

@app.route('/search/by/catgory', methods=['POST'])
def searchByCategory():
    # Get the search query parameters from the request
    data = request.get_json()
    query = data.get('query')
    print(query, "printed query word")

    # Search for products and categories based on the query
    products = Product.query.filter(or_(
        Product.name.ilike(f'%{query}%'),
        Product.rpu.ilike(f'%{query}%'),
        Product.manufacture.ilike(f'%{query}%'),
        Product.description.ilike(f'%{query}%'),
        Product.expiry.ilike(f'%{query}%'),
        Product.category.has(Category.name.ilike(f'%{query}%'))
    )).all()
    category = Category.query.filter_by(name=query).first()
    products = Product.query.filter_by(category_id=category.id).all()
    product_list = []
    categories=[]
    for new_product in products:
        prod_data = {
            'id': new_product.id,
            'quantity': new_product.quantity,
            'name': new_product.name,
            'manufacture': new_product.manufacture,
            'expiry': new_product.expiry,
            'description': new_product.description,
            'rpu': new_product.rpu,
            'unit': new_product.unit,
            'image': base64.b64encode(new_product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
        }
        if new_product.category not in categories:
            categories.append(new_product.category)
        product_list.append(prod_data)
    categories_list = []
    for category in categories:
        cat = {
            'id': category.id,
            'name': category.name,
        }
        categories_list.append(cat)
    return jsonify({"cat":categories_list, 'pro':product_list}), 200
@app.route('/search/for', methods=['POST'])
def search():
    # Get the search query parameters from the request
    data = request.get_json()
    query = data.get('query')
    print(query, "printed query word")

    # Search for products and categories based on the query
    products = Product.query.filter(or_(
        Product.name.ilike(f'%{query}%'),
        Product.rpu.ilike(f'%{query}%'),
        Product.manufacture.ilike(f'%{query}%'),
        Product.description.ilike(f'%{query}%'),
        Product.expiry.ilike(f'%{query}%'),
        Product.category.has(Category.name.ilike(f'%{query}%'))
    )).all()
    product_list = []
    categories=[]
    for new_product in products:
        prod_data = {
            'id': new_product.id,
            'quantity': new_product.quantity,
            'name': new_product.name,
            'manufacture': new_product.manufacture,
            'expiry': new_product.expiry,
            'description': new_product.description,
            'rpu': new_product.rpu,
            'unit': new_product.unit,
            'image': base64.b64encode(new_product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
        }
        if new_product.category not in categories:
            categories.append(new_product.category)
        product_list.append(prod_data)
    categories_list = []
    for category in categories:
        cat = {
            'id': category.id,
            'name': category.name,
        }
        categories_list.append(cat)
    return jsonify({"cat":categories_list, 'pro':product_list}), 200

@main.route('/')
def index():
    return render_template('index.html')

@cache.cached(timeout=50, key_prefix="get_products")
@app.route('/get/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        product_list = []
        for new_product in products:
            prod_data = {
                'id': new_product.id,
                'quantity': new_product.quantity,
                'name': new_product.name,
                'manufacture': new_product.manufacture,
                'expiry': new_product.expiry,
                'description': new_product.description,
                'rpu': new_product.rpu,
                'unit': new_product.unit,
                'image': base64.b64encode(new_product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
            }        
            product_list.append(prod_data)
        return jsonify(product_list),200
    except Exception as e:
        return jsonify({'error': str(e)})

@cache.cached(timeout=50, key_prefix="get_category")    
@app.route('/get/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        categories_list = []
        for category in categories:
            cat = {
                'id': category.id,
                'name': category.name,
            }
            categories_list.append(cat)
        return jsonify(categories_list)
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/update/order/<int:id>', methods=['PUT'])
def update_order(id):
    data = request.get_json()
    order = Order.query.filter_by(id=id).first()
    order.rate = data['value']
    db.session.commit()
    cat = {
        'id': order.id,
        'product_name': order.product_name,
        'user_id': order.user_id,
        'quantity': order.quantity,
        'total': order.total,
        'rate': order.rate,
        'image': base64.b64encode(order.image).decode('utf-8') if order.image else None,
        'order_date': order.order_date.strftime("%Y-%m-%d")
    }
    orders = Order.query.filter_by(product_name=order.product_name).all()
    avg_rate = int(sum([each_order.rate for each_order in orders])/len(orders))
    product = Product.query.filter_by(name = order.product_name).first()
    print(avg_rate,"Average rating")
    product.rate = avg_rate
    db.session.commit()
    return jsonify({'message': 'Created request', 'resource':cat}), 201        
    
@app.route('/get/orders', methods=['GET'])
def get_orders():
    try:
        orders = Order.query.filter_by(user_id=current_user.id).all()
        orders_list = []
        for order in orders:
            cat = {
                'id': order.id,
                'product_name': order.product_name,
                'user_id': order.user_id,
                'quantity': order.quantity,
                'rate': order.rate,
                'total': order.total,
                'image': base64.b64encode(order.image).decode('utf-8') if order.image else None,
                'order_date': order.order_date.strftime("%Y-%m-%d")
            }
            orders_list.append(cat)
        return jsonify(orders_list),200
    except Exception as e:
        return jsonify({'error': str(e)})

@main.route('/add/to/cart', methods=['POST'])
# @login_required
def add_to_cart():
    data = request.get_json()
    product_exist = Cart.query.filter_by(product_id=int(data['id'])).first()
    product = Product.query.filter_by(id=int(data['id'])).first()
    if product_exist:
        print("hello moto")
        if product.quantity>product_exist.quantity:
            print("item increasing")
            product_exist.quantity+=1
            db.session.commit()
            cart_list = {
                'id':product_exist.id,  
                'product_id':product_exist.product_id,  
                'product_name':product_exist.product_name,  
                'rpu':product_exist.rpu,  
                'quantity':product_exist.quantity, 
                'user_id':product_exist.user_id 
            }
            return jsonify({"message": "added to cart", 'resource':cart_list}), 209
        return jsonify({"message": "No more qty available"}), 200
    else:
        print("hello patlu")
        if product.quantity>0:
            cart_item = Cart(product_id=product.id, product_name=product.name, rpu=product.rpu, quantity=1, user_id=current_user.id)
            db.session.add(cart_item)
            db.session.commit()
            cart_list = {
                'id':cart_item.id,
                'product_id':cart_item.product_id,  
                'product_name':cart_item.product_name,  
                'rpu':cart_item.rpu,  
                'quantity':cart_item.quantity, 
                'user_id':cart_item.user_id 
            }
            return jsonify({"message": "added to cart", 'resource':cart_list}), 201
        else:
            return jsonify({"message": "No more qty available"}), 200
        
@main.route('/get/cart/items')
@login_required
def get_cart_items():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_list=[]
    for product_exist in cart_items:
        cart = {
            'id':product_exist.id,  
            'product_id':product_exist.product_id,  
            'product_name':product_exist.product_name,  
            'rpu':product_exist.rpu,  
            'quantity':product_exist.quantity, 
            'user_id':product_exist.user_id 
        }
        cart_list.append(cart)
    return jsonify(cart_list), 200

@main.route('/cart/item/remove/<int:id>', methods=['DELETE'])
@login_required
def cart_item_remove(id):
    cart_item = Cart.query.filter_by(id=id).first()
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message':"remove item", "resource":id}), 200

@main.route('/cart/item/increment/<int:id>', methods=['PUT'])
# @login_required
def cart_item_increment(id):
    cart_item = Cart.query.filter_by(id=id).first()
    product = Product.query.filter_by(id = cart_item.product_id).first()
    if product.quantity> cart_item.quantity:
        cart_item.quantity+=1
        db.session.commit()
        cart_list = {
            'id':cart_item.id,  
            'product_id':cart_item.product_id,  
            'product_name':cart_item.product_name,  
            'rpu':cart_item.rpu,  
            'quantity':cart_item.quantity, 
            'user_id':cart_item.user_id 
        }
        return jsonify({"message": "added to cart", 'resource':cart_list}), 201
    return jsonify({"message": "No more qty available"}), 200

@main.route('/cart/items/buy')
# @login_required
def cart_items_buy():
    cart_item = Cart.query.filter_by(user_id=current_user.id).all()
    for cart in cart_item:
        product = Product.query.filter_by(id=cart.product_id).first()
        order = Order(product_name=cart.product_name, user_id=current_user.id, quantity=cart.quantity, total=cart.quantity*cart.rpu, order_date=datetime.now(), image=product.image, rate=0)
        db.session.add(order)
        db.session.commit()
        db.session.delete(cart)
        db.session.commit()
        product.quantity-=cart.quantity
        db.session.commit()
    return jsonify({"message": "Thank you for shopping, visit again", 'resource':[]}), 200

@main.route('/cart/item/decrement/<int:id>', methods=['PUT'])
# @login_required
def cart_item_decrement(id):
    cart_item = Cart.query.filter_by(id=id).first()
    if cart_item.quantity>1:
        cart_item.quantity-=1
        db.session.commit()
        cart_list = {
            'id':cart_item.id,  
            'product_id':cart_item.product_id,  
            'product_name':cart_item.product_name,  
            'rpu':cart_item.rpu,  
            'quantity':cart_item.quantity, 
            'user_id':cart_item.user_id 
        }
        return jsonify({"message": "added to cart", 'resource':cart_list}), 201
    else:
        cart_item = Cart.query.filter_by(id=id).first()
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message':"remove item", "resource":id}), 200

# @login_required
# @role_required("admin")
@main.route('/add/cat', methods=['POST'])
def create():
    data = request.get_json()
    if data:
        if not Category.query.filter_by(name=data['name']).first():
            if current_user.role=='manager':
                admin = User.query.filter_by(role='admin').first()
                message = data['name']
                requested = RequestResponse(status='pending',
                                            type='category',
                                            message=message,
                                            sender=current_user.email,
                                            receiver=admin.email,
                                            timestamp=datetime.now())
                db.session.add(requested)
                db.session.commit()
                noti_data = {
                    'id': requested.id,
                    'state': requested.status,
                    'message': requested.message,
                    'sender': requested.sender,
                    'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                }
                return jsonify({'message': 'Created request', 'resource':noti_data}), 201   
            else:             
                category=Category(name=data['name'])
                db.session.add(category)
                db.session.commit()
                return jsonify({'message':f"Category {data['name']} created successfully",
                                'resource':{'id':category.id,'name':category.name}}), 201
        abort(409, message="Resource already exists")
    else:
        abort(404, message="Not found")
               
# @login_required
# @role_required("admin")
@main.route('/update/<int:cat_id>', methods=['GET', 'PUT', 'DELETE'])
def update(cat_id):
    if isinstance(cat_id, int):
        if request.method=='GET':
            category=Category.query.filter_by(id=cat_id).first()
            if category:
                cat = { 
                    'id': category.id,
                    'name': category.name,
                }
                return jsonify(cat)
            else:
                abort(404, message="Not found")
        if request.method=='PUT':
            data=request.get_json()
            category=Category.query.filter_by(id=cat_id).first()
            if current_user.role=='manager':
                admin = User.query.filter_by(role='admin').first()
                message = f"{cat_id},{data['name']}"
                requested = RequestResponse(status='pending',
                                            type='category update',
                                            message=message,
                                            sender=current_user.email,
                                            receiver=admin.email,
                                            timestamp=datetime.now())
                db.session.add(requested)
                db.session.commit()
                noti_data = {
                    'id': requested.id,
                    'state': requested.status,
                    'message': requested.message,
                    'sender': requested.sender,
                    'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                }
                return jsonify({'message': 'Created request', 'resource':noti_data}), 201                    
            else:
                category.name=data['name']
                db.session.commit()
                return jsonify({'message':f"Category {data['name']} update successfully in database",'resource':{'id':category.id,'name':category.name}}), 201
        if request.method=='DELETE':
            category=Category.query.filter_by(id=cat_id).first()
            if category:
                if current_user.role=='manager':
                    admin = User.query.filter_by(role='admin').first()
                    message = f"{cat_id},{category.name}"
                    requested = RequestResponse(status='pending',
                                                type='category delete',
                                                message=message,
                                                sender=current_user.email,
                                                receiver=admin.email,
                                                timestamp=datetime.now())
                    db.session.add(requested)
                    db.session.commit()
                    noti_data = {
                        'id': requested.id,
                        'state': requested.status,
                        'message': requested.message,
                        'sender': requested.sender,
                        'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                    }
                    return jsonify({'message': 'Created request', 'resource':noti_data}), 201                    
                else:
                    products = Product.query.filter_by(category_id=int(cat_id)).all()
                    for product in products:
                        carts = Cart.query.filter_by(product_id=product.id).all()
                        for cart in carts:
                            db.session.delete(cart)
                            db.session.commit()
                        db.session.delete(product)
                        db.session.commit()                    
                    db.session.delete(category)
                    db.session.commit()
                    return jsonify({'message':f"Category { category.name } Deleted successfully from database", 'resource':{'id':category.id,'name':category.name}}), 201
            return jsonify({'message':"Not found"}), 404
    else:
        return '', 400

@main.route('/update/product/<int:prod_id>', methods=['GET', 'PUT', 'DELETE'])
def update_product(prod_id):
    if isinstance(prod_id, int):
        if request.method == 'GET':
            product = Product.query.filter_by(id=prod_id).first()
            if product:
                prod_data = {
                    'id': product.id,
                    'quantity': product.quantity,
                    'name': product.name,
                    'manufacture': product.manufacture,
                    'description': product.description,
                    'expiry': product.expiry,
                    'rpu': product.rpu,
                    'unit': product.unit,
                    'image': base64.b64encode(product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
                }        
                return jsonify(prod_data),200            
            else:
                abort(404, message="Not found")
        elif request.method == 'PUT':
            product = Product.query.filter_by(id=prod_id).first()
            if product:
                if current_user.role=='manager':
                    admin = User.query.filter_by(role='admin').first()
                    message = f"{prod_id},{request.form['name']},{request.form['quantity']},{request.form['manufacture']},{request.form['expiry']},{request.form['rpu']},{request.form['category_id']},{request.form['unit']}, {request.form['description']}"
                    requested = RequestResponse(status='pending',
                                                type='product update',
                                                message=message,
                                                sender=current_user.email,
                                                image=request.files['image'].read(),
                                                receiver=admin.email,
                                                timestamp=datetime.now())
                    db.session.add(requested)
                    db.session.commit()
                    noti_data = {
                        'id': requested.id,
                        'state': requested.status,
                        'message': requested.message,
                        'sender': requested.sender,
                        'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                    }
                    return jsonify({'message': 'Created request', 'resource':noti_data}), 201
                else:                   
                    product.name = request.form['name']
                    product.quantity = int(request.form['quantity'])
                    product.manufacture = datetime.strptime(request.form['manufacture'], '%Y-%m-%d')
                    product.expiry = datetime.strptime(request.form['expiry'], '%Y-%m-%d')
                    product.rpu = float(request.form['rpu'])
                    product.category_id = float(request.form['category_id'])
                    product.unit = request.form['unit']
                    product.description = request.form['description']
                    
                    # Handle file upload
                    product.image = request.files['image'].read()
                    db.session.commit()
                    prod_data = {
                        'id': product.id,
                        'quantity': product.quantity,
                        'name': product.name,
                        'manufacture': product.manufacture,
                        'expiry': product.expiry,
                        'description': product.description,
                        'rpu': product.rpu,
                        'unit': product.unit,
                        'image': base64.b64encode(product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
                    }        
                    return jsonify({'message': f"Product {request.form['name']} updated successfully in the database",
                                    'resource': prod_data}), 201
            else:
                return jsonify({'message': "Not found"}), 404
        elif request.method == 'DELETE':
            product = Product.query.filter_by(id=prod_id).first()
            if product:
                if current_user.role=='manager':
                    admin = User.query.filter_by(role='admin').first()
                    message = f"{prod_id},{product.name}"
                    requested = RequestResponse(status='pending',
                                                type='product delete',
                                                message=message,
                                                sender=current_user.email,
                                                receiver=admin.email,
                                                timestamp=datetime.now())
                    db.session.add(requested)
                    db.session.commit()
                    noti_data = {
                        'id': requested.id,
                        'state': requested.status,
                        'message': requested.message,
                        'sender': requested.sender,
                        'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                    }
                    return jsonify({'message': 'Created request', 'resource':noti_data}), 201
                else:
                    carts = Cart.query.filter_by(product_id=product.id).all()
                    for cart in carts:
                        db.session.delete(cart)
                        db.session.commit()
                    db.session.delete(product)
                    db.session.commit()
                    return jsonify({'message': f"Product {product.name} deleted successfully from the database", 'resource':prod_id}), 201
            return jsonify({'message': "Not found"}), 404
    else:
        return '', 400
@main.route('/update/profile/<int:id>', methods=['PUT'])
def update_profile(id):
    if isinstance(id, int):
        if request.method == 'PUT':
            user = User.query.filter_by(id=id).first()
            if user:
                # Handle file upload
                user.image = request.files['image'].read()
                db.session.commit()
                user_data = {
                    'id': user.id,
                    'role': user.role,
                    'email': user.email,
                    'auth_token': current_user.is_authenticated,
                    'image': base64.b64encode(user.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
                }        
                return jsonify({'message': f"User profile updated successfully in the database",
                                'resource': user_data}), 201
            else:
                return jsonify({'message': "Not found"}), 404
    else:
        return '', 400
@main.route('/get/all/managers', methods=['GET'])
def all_man():
    if request.method == 'GET':
        managers = User.query.filter_by(role='manager').all()
        man_list=[]
        for man in managers:
            print((datetime.now() - man.doj).total_seconds() / (365.25 * 24 * 3600),"year of exprience")
            man_data = {
                'id': man.id,
                'role': man.role,
                'name': man.name,
                'email': man.email,
                'doj': man.doj.strftime('%Y-%m-%d'),
                'exp': f"{(datetime.now() - man.doj).total_seconds() / (365.25 * 24 * 3600):.2f} years of experience",
                'image': base64.b64encode(man.image).decode('utf-8') if man.image else None # Assuming image is stored as a base64-encoded string
            }
            man_list.append(man_data)       
        return jsonify({'resource': man_list}), 200
@main.route('/get/all/noti', methods=['GET'])
def all_noti():
    if request.method == 'GET':
        if current_user.role=='admin':
            notis = RequestResponse.query.filter_by(status='pending').all()
            noti_list=[]
            for noti in notis:
                noti_data = {
                    'id': noti.id,
                    'state': noti.status,
                    'message': noti.message,
                    'sender': noti.sender,
                    'timestamp': noti.timestamp.strftime('%Y-%m-%d'),
                }
                noti_list.append(noti_data)       
            return jsonify({'resource': noti_list}), 200
        else:
            notis = RequestResponse.query.filter_by(sender=current_user.email, status='pending').all()
            noti_list=[]
            for noti in notis:
                noti_data = {
                    'id': noti.id,
                    'state': noti.status,
                    'message': noti.message,
                    'sender': noti.sender,
                    'timestamp': noti.timestamp.strftime('%Y-%m-%d'),
                }
                noti_list.append(noti_data)       
            return jsonify({'resource': noti_list}), 200


@main.route('/auth/user', methods=['GET'])
def auth_user():
    if request.method == 'GET':
        if current_user.is_authenticated:
            user_data = {
                'id': current_user.id,
                'role': current_user.role,
                'email': current_user.email,
                'auth_token': current_user.is_authenticated,
                'image': base64.b64encode(current_user.image).decode('utf-8') if current_user.image else None  # Assuming image is stored as a base64-encoded string
            }        
            return jsonify({'message': f"User profile updated successfully in the database",
                            'resource': user_data}), 200
        else:
            return jsonify({'message': "Not found"}), 404


@main.route('/add/product', methods=['POST'])
@login_required
@role_required("admin")
def product():
    if request.method=='POST':
        name_exist = Product.query.filter_by(name=request.form['name']).first()
        if name_exist:
            return jsonify({'message': "Resource already exists"}), 409
        else:
            if current_user.role=='manager':
                admin = User.query.filter_by(role='admin').first()
                message = f"{request.form['name']},{request.form['quantity']},{request.form['manufacture']},{request.form['expiry']},{request.form['rpu']},{request.form['category_id']},{request.form['unit']}, {request.form['description']}"
                requested = RequestResponse(status='pending',
                                            type='product',
                                            message=message,
                                            sender=current_user.email,
                                            image = request.files['image'].read(),
                                            receiver=admin.email,
                                            timestamp=datetime.now())
                db.session.add(requested)
                db.session.commit()
                noti_data = {
                    'id': requested.id,
                    'state': requested.status,
                    'message': requested.message,
                    'sender': requested.sender,
                    'timestamp': requested.timestamp.strftime('%Y-%m-%d'),
                }
                return jsonify({'message': 'Created request', 'resource':noti_data}), 201
            else:
                name = request.form['name']
                quantity = int(request.form['quantity'])
                manufacture = datetime.strptime(request.form['manufacture'], '%Y-%m-%d')
                expiry = datetime.strptime(request.form['expiry'], '%Y-%m-%d')
                rpu = float(request.form['rpu'])
                category_id = float(request.form['category_id'])
                unit = request.form['unit']
                description = request.form['description']
                
                # Handle file upload
                image = request.files['image'].read()
                new_product = Product(
                    name=name,
                    quantity=quantity,
                    manufacture=manufacture,
                    expiry=expiry,
                    description=description,
                    rpu=rpu,
                    unit=unit,
                    image=image,
                    category_id=category_id
                )
                prod_data = {
                    'id': new_product.id,
                    'quantity': new_product.quantity,
                    'name': new_product.name,
                    'manufacture': new_product.manufacture,
                    'expiry': new_product.expiry,
                    'description': new_product.description,
                    'rpu': new_product.rpu,
                    'unit': new_product.unit,
                    'image': base64.b64encode(new_product.image).decode('utf-8')  # Assuming image is stored as a base64-encoded string
                }        
                db.session.add(new_product)
                db.session.commit()
                return jsonify({'message': f"Product {request.form['name']} add successfully in the database",
                                'resource': prod_data}), 201

#-------------------authentication and authorization-----------------#
auth = Blueprint('auth', __name__)

@auth.route('/api/login', methods=['POST'])
def login_post():
    # login code goes here
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({'error': 'wrong credentials'}), 404 # if the user doesn't exist or password is wrong, reload the page
    else:
        print("verified user")
        print(data['remember'])
        user_data = {
                    'id': user.id,
                    'role': user.role,
                    'email': user.email,
                    'auth_token': current_user.is_authenticated,
                    'image': base64.b64encode(user.image).decode('utf-8') if user.image else None  # Assuming image is stored as a base64-encoded string
                }  
        user.loginAt=datetime.now()
        db.session.commit()
        if data['remember']:
            login_user(user, remember=True)
        else:
            login_user(user, remember=False)
        return jsonify({'message': 'User login successfully', 'resource': user_data}), 200
    
@auth.route('/auth/user')
def auth_user():

    if not current_user.is_authenticated:
        return jsonify({'error': 'wrong credentials'}), 404 # if the user doesn't exist or password is wrong, reload the page
    else:
        user_data = {
                    'id': current_user.id,
                    'role': current_user.role,
                    'email': current_user.email,
                    'auth_token': current_user.is_authenticated,
                    'image': base64.b64encode(current_user.image).decode('utf-8') if current_user.image else None  # Assuming image is stored as a base64-encoded string
                }  
        return jsonify({'message': 'User login successfully', 'resource': user_data}), 200
    
@auth.route('/decline/<int:id>', methods=['GET'])
def decline(id):
    req = RequestResponse.query.filter_by(id=id).first()
    if req:
        req.status='declined'
        db.session.commit()
        return jsonify({'message': 'Request declined'}), 200
    else:
        return jsonify({'message': 'Not found'}), 404
    
@auth.route('/delete/man/<int:id>', methods=['DELETE'])
def delete_man(id):
    man = User.query.filter_by(id=id).first()
    if man:
        db.session.delete(man)
        db.session.commit()
        return jsonify({'message': 'Deleted manager', 'resource':id}), 200
    else:
        return jsonify({'message': 'Not found'}), 404
    
@auth.route('/signup', methods=['POST'])
def signup_post():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first() # if this returns a user, then the email already exists in database
    exist_req = RequestResponse.query.filter_by(sender=data["email"]).first() # if this returns a user, then the email already exists in database
    admin = User.query.filter_by(role='admin').first() # if this returns a user, then the email already exists in database
    if user or exist_req: # if a user is found, we want to redirect back to signup page so user can try again
        return jsonify({'error': 'User already exists'}), 409
    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    if data["role"]=='manager':
        message = f"{data['email']},{data['name']},{data['role']},{data['password']}"
        requested = RequestResponse(status='pending',
                                    type='manager',
                                    message=message,
                                    sender=data['email'],
                                    receiver=admin.email,
                                    timestamp=datetime.now())
        db.session.add(requested)
        db.session.commit()
        return jsonify({'message': 'Created request, on result will send on mail'}), 201
    else:
        new_user = User(email=data["email"], name=data["name"], role=data["role"], password=generate_password_hash(data["password"],method='scrypt'), doj=datetime.now())
        db.session.add(new_user)
        db.session.commit()
        verified_data = {
            "email": data["email"],
            "name": data["name"],
            "role": data["role"],
            "auth-token": current_user.is_authenticated
        }
        return jsonify({'message': 'User registered successfully', 'data': verified_data}), 201

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message':"logout successful"}),200

app.register_blueprint(auth)
app.register_blueprint(main)

login_manager = LoginManager()
login_manager.init_app(app)

from backendjobs.admin import *

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.filter_by(id=int(user_id)).first()
if __name__=='__main__':
    app.run(debug=True)