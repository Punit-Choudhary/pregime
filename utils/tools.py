from app import calorie_collection, nutrients_collection, user_collection
import utils.date as date


def update(username, user_collection):
  # get user's data
  user_details = user_collection.find_one({"_id": username})

  # update day
  today = int(date.get_yday())

  if today != user_details['last_sync']:
    # New Day
    daily_setup(user_details['bmi'], user_details['weight'],
                user_details['trimester'], today, username)

  day = int(user_details['day']) + today - int(user_details['last_sync'])

  # update trimester
  if day <= 90:
    trimester = 1
  elif day <= 180:
    trimester = 2
  elif day <= 300:
    trimester = 3

  user_collection.update_one(
    {"_id": username},
    {"$set": {
      "day": day,
      "trimester": trimester,
      "last_sync": today
    }})


def daily_setup(bmi, weight, trimester, today, username):
  calorie_collection.update_one({"_id": username}, {
    "$set": {
      str(int(today)): {
        "total": 0,
        "daily_goal": calorie_goal(bmi, weight, trimester),
        "meals": []
      }
    }
  })

  nutrients_daily_goal = nutrients_goal()

  nutrients_collection.update_one({"_id": username}, {
    "$set": {
    str(int(today)): {
      "carbs": 0,
      "carbs_goal": nutrients_daily_goal['carbs'],
      "fat": 0,
      "fat_goal": nutrients_daily_goal['fat'],
      "protein": 0,
      "protein_goal": nutrients_daily_goal['protein'],
      "calcium": 0,
      "calcium_goal": nutrients_daily_goal['calcium'],
      "iron": 0,
      "iron_goal": nutrients_daily_goal['iron']
    }}
  })


def calorie_goal(bmi, weight, trimester):
  if bmi < 19.8:
    cal = [30, 35, 40][trimester - 1]
  elif bmi > 19.8 and bmi < 26:
    cal = [25, 30, 34][trimester - 1]
  elif bmi > 26.1 and bmi < 29:
    cal = [20, 24, 30][trimester - 1]
  else:
    cal = [8, 12, 18][trimester - 1]

  cal *= weight

  return cal


def nutrients_goal():
  return {
    "carbs": 175,  #g
    "fat": 15,  #g
    "protein": 71,  #g
    "calcium": 1.3,  #g
    "iron": 50  #mg
  }
