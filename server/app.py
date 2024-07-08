#!/usr/bin/env python3
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_migrate import Migrate
import os

from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
       restaurants=Restaurant.query.all()
       return jsonify([restaurant.to_dict() for restaurant in restaurants])
    
class RestaurantById(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant:
            restaurant_dict = restaurant.to_dict()
    
            pizzas = []
            for rp in restaurant.restaurant_pizzas:
                pizza_details = {
                    "id": rp.id,
                    "pizza": {
                        "id": rp.pizza.id,
                        "name": rp.pizza.name,
                        "ingredients": rp.pizza.ingredients
                    },
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant_id
                }
                pizzas.append(pizza_details)
            restaurant_dict['restaurant_pizzas'] = pizzas
            return jsonify(restaurant_dict)
        else:
            response_data = {"error": "Restaurant not found"}
            return make_response(jsonify(response_data), 404)

    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            response = make_response(jsonify({"message": "Restaurant deleted"}), 204)
        else:
            response = make_response(jsonify({"error": "Restaurant not found"}), 404)

        return response

class Pizzas(Resource):
    def get(self):
        response = [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in Pizza.query.all()]
        return make_response(jsonify(response), 200)

class RestaurantPizzaResource(Resource):
    def post(self):
        data = request.get_json()

        try:
            restaurant_id = data['restaurant_id']
            pizza_id = data['pizza_id']
            price = data['price']

            if price < 1 or price > 30:
                return make_response(jsonify({"errors": ["validation errors"]}), 400)

            new_restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )

            db.session.add(new_restaurant_pizza)
            db.session.commit()

            response = new_restaurant_pizza.to_dict()
            return make_response(jsonify(response), 201)

        except KeyError as e:
            return make_response(jsonify({"errors": [f"Missing key: {str(e)}"]}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"errors": [str(e)]}), 400)
        finally:
            db.session.close()

api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantById, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzaResource, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
