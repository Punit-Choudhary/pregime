import twilio_api
from bson.json_util import dumps
import re
import os
import utils.date as date
import utils.tools as tools
from datetime import timedelta
from flask import (Flask, render_template, make_response, redirect, request)
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required,
                                verify_jwt_in_request)
from pymongo import MongoClient

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)

jwt = JWTManager(app)

# -- Database Setup -- #

client = MongoClient(os.environ['MONGO_URI'], serverSelectionTimeoutMS=5000)
dbs = client['PregimeDB']
user_collection = dbs['USER']
calorie_collection = dbs['CALORIE']
nutrients_collection = dbs['NUTRIENTS']
food_collection = dbs['FOOD']
aasha_collection = dbs['AASHA']

# -- Database Setup Ends -- #


@jwt.unauthorized_loader
def custom_unauthorized_response(_err):
  return redirect('/login')


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
  return redirect('/login')


@app.route('/')
@jwt_required(locations='cookies')
def home():
  username = get_jwt_identity()
  tools.update(username, user_collection)

  return render_template('home.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
  if request.method == 'GET':
    return render_template('login.html', ctx={})
  elif request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')

    print(username, password)

    user_details = user_collection.find_one({"_id": username})

    if user_details:
      if password == user_details['password']:
        access_token = create_access_token(identity=username)
        resp = make_response(redirect('/'))
        resp.set_cookie('access_token_cookie', access_token)
        return resp

    ctx = {'error': 'Incorrect Username or Password'}
    return render_template('login.html', ctx=ctx)


@app.route('/register/', methods=['GET', 'POST'])
def register():
  if request.method == 'GET':
    ctx = {}
    return render_template('register.html', ctx=ctx)
  elif request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    phno = request.form['phno']
    city = request.form['city']
    weight = float(request.form['weight'])
    height = int(request.form['height'])
    age = request.form['age']
    week = request.form['week']

    register_yday = date.get_yday()
    day = (7 * int(week)) - 6

    if day <= 90:
      trimester = 1
    elif day <= 180:
      trimester = 2
    elif day <= 300:
      trimester = 3

    height /= 100
    bmi = weight / (height**2)

    data = {
      "_id": username,
      "password": password,
      "name": name,
      "phno": phno,
      "city": city,
      "weight": weight,
      "height": height,
      "bmi": bmi,
      "age": age,
      "register_yday": int(register_yday),
      "last_sync": int(register_yday),
      "day": day,
      "trimester": trimester,
      "emergency": []
    }

    # Add to Database
    user_collection.insert_one(data)

    # Make entry in Calories and Nutrients collection
    calorie_data = {
      "_id": username,
      str(int(register_yday)): {
        "total": 0,
        "daily_goal": tools.calorie_goal(height, weight, trimester),
        "meals": []
      }
    }

    calorie_collection.insert_one(calorie_data)

    nutrients_goal = tools.nutrients_goal()
    nutrients_data = {
      "_id": username,
      str(int(register_yday)): {
        "carbs": 0,
        "carbs_goal": nutrients_goal['carbs'],
        "fat": 0,
        "fat_goal": nutrients_goal['fat'],
        "protein": 0,
        "protein_goal": nutrients_goal['protein'],
        "calcium": 0,
        "calcium_goal": nutrients_goal['calcium'],
        "iron": 0,
        "iron_goal": nutrients_goal['iron']
      }
    }

    nutrients_collection.insert_one(nutrients_data)

    # Login user
    access_token = create_access_token(identity=username)
    resp = make_response(redirect('/'))
    resp.set_cookie('access_token_cookie', access_token)

    return resp


@app.route('/logout')
@jwt_required(locations='cookies')
def logout():
  resp = make_response(redirect('/login'))
  resp.set_cookie('access_token_cookie', '', expires=0)

  return resp


# -- Emergency -- #
@app.route('/add/emergency/<phno>/')
@jwt_required(locations='cookies')
def add_emergency(phno):
  username = get_jwt_identity()

  user_collection.update_one({"_id": username}, {"$push": {"emergency": phno}})

  return redirect('/')


@app.route('/remove/emergency/<phno>/')
@jwt_required(locations='cookies')
def remove_emergency(phno):
  username = get_jwt_identity()

  user_collection.update_one({"_id": username}, {"$pull": {"emergency": phno}})

  return redirect('/')


@app.route('/emergency/')
@jwt_required(locations='cookies')
def emergency():
  username = get_jwt_identity()

  emergency_list = user_collection.find_one({"_id": username})['emergency']

  return emergency_list


# -- Emergency Ends -- #


@app.route('/contactaasha', methods=['GET', 'POST'])
@jwt_required(locations='cookies')
def contact_aasha():
  username = get_jwt_identity()

  if request.method == 'GET':
    # get user's city
    city = user_collection.find_one({"_id": username})['city']

    # fetch aasha details
    aasha_details = aasha_collection.find_one({"_id": city})

    return aasha_details
  elif request.method == 'POST':
    name = request.form['name']
    phno = request.form['phno']
    city = request.form['city']

    data = {"_id": city, "name": name, "phno": phno}

    aasha_collection.insert_one(data)
    return redirect('/')


# -- Food -- #


@app.route('/add/food')
@jwt_required(locations='cookies')
def add_food():
  barcode = request.json.get('barcode')
  name = request.json.get('name')
  imgUrl = request.json.get('imgUrl')
  about = request.json.get('about')
  healthy = request.json.get('healthy')
  suggestions = request.json.get('suggestions')
  calorie = request.json.get('calorie')
  # Carbs, Fat, Protein, Calcium, Iron
  nutrients = request.json.get('nutrients')
  weight = request.json.get('weight')

  data = {
    "_id": barcode,
    "name": name.lower(),
    "imgUrl": imgUrl,
    "about": about,
    "healthy": healthy,
    "suggestions": suggestions,
    "weight": weight,
    "calorie": calorie,
    "nutrients": {
      "carbs": nutrients['carbs'],
      "fat": nutrients['fat'],
      "protein": nutrients['protein'],
      "calcium": nutrients['calcium'],
      "iron": nutrients['iron']
    }
  }

  food_collection.insert_one(data)
  return "Done"


@app.route('/food/<barcode>')
@jwt_required(locations='cookies')
def food(barcode):
  food_details = food_collection.find_one({"_id": barcode})
  return food_details


@app.route('/search', methods=['POST'])
@jwt_required(locations='cookies')
def search():
  query = request.form['query']
  data = food_collection.find({"about": {"$regex": query}})

  data = list(data)

  return data


@app.route('/consume/<barcode>')
@jwt_required(locations='cookies')
def consume(barcode):
  username = get_jwt_identity()

  food_details = food_collection.find_one({"_id": barcode})

  weight = food_details['weight']
  cal = (food_details['calorie'] / 100) * weight

  nutrients = food_details['nutrients']
  carbs = (nutrients['carbs'] / 100) * weight
  fat = (nutrients['fat'] / 100) * weight
  protein = (nutrients['protein'] / 100) * weight
  calcium = (nutrients['calcium'] / 100) * weight
  iron = (nutrients['iron'] / 100) * weight

  today = str(int(date.get_yday()))
  cal_data = calorie_collection.find_one({"_id": username})
  print(cal_data)

  cal_value = int(cal_data[today]['total']) + cal

  nutri_data = nutrients_collection.find_one({"_id": username})
  carb_value = int(nutri_data[today]['carbs']) + carbs
  fat_value = int(nutri_data[today]['fat']) + fat
  protein_value = int(nutri_data[today]['protein']) + protein
  calcium_value = int(nutri_data[today]['calcium']) + calcium
  iron_value = int(nutri_data[today]['iron']) + iron

  # Add the food in meal section
  calorie_collection.update_one({"_id": username}, {
    "$push": {
      f"{today}.meals": barcode
    },
    "$set": {
      f"{today}.total": cal_value
    }
  })

  nutrients_collection.update_one({"_id": username}, {
    "$set": {
      f"{today}.carbs": carb_value,
      f"{today}.fat": fat_value,
      f"{today}.protein": protein_value,
      f"{today}.calcium": calcium_value,
      f"{today}.iron": iron_value
    }
  })

  return redirect('/')


def suggested_food(cal):
  food_data = food_collection.find({"calorie": {"$lt": 25}, "healthy": True})

  if food_data:
    return food_data
  else:
    "Not Found"


# -- Food Ends -- #

if __name__ == "__main__":
  app.run('0.0.0.0', port=5500, debug=True)
