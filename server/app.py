#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [restaurant.to_dict(rules=('-restaurant_pizzas',)) for restaurant in restaurants]

class RestaurantById(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            return restaurant.to_dict()
        return {'error': 'Restaurant not found'}, 404
    
    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return '', 204
        return {'error': 'Restaurant not found'}, 404

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict(rules=('-restaurant_pizzas',)) for pizza in pizzas]

class RestaurantPizzasResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            if not data:
                return {'errors': ['validation errors']}, 400
                
            # Validate required fields
            required_fields = ['price', 'pizza_id', 'restaurant_id']
            if not all(field in data for field in required_fields):
                return {'errors': ['validation errors']}, 400
            
            # Validate price before creating object
            price = data.get('price')
            if price is None or not (1 <= price <= 30):
                return {'errors': ['validation errors']}, 400
            
            # Create new RestaurantPizza - will also trigger validation
            restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=data['pizza_id'],
                restaurant_id=data['restaurant_id']
            )
            
            db.session.add(restaurant_pizza)
            db.session.commit()
            
            # Return the created RestaurantPizza with nested data
            return restaurant_pizza.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            # Return generic validation error for any exception
            return {'errors': ['validation errors']}, 400

api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantById, '/restaurants/<int:id>')
api.add_resource(Pizzas, '/pizzas')
api.add_resource(RestaurantPizzasResource, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)
