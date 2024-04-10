from pymongo import MongoClient
import csv

def unique_wine():
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')

    db = client['TasteBud']

    collection = db.wines

    unique_types = collection.distinct('type')
    unique_types_count = len(unique_types)
    print("Unique types:", unique_types_count)
    print(unique_types)



def food_consistency():
    input_csv_file = 'wine_data3.csv'
    type_food_mapping = {}
    inconsistencies = {}

    with open(input_csv_file, mode='r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            wine_type = row['type']
            wine_id = row['id']
            food_ids = row['food_ids']
            if wine_type in type_food_mapping:
                if type_food_mapping[wine_type] != food_ids:
                    if wine_type not in inconsistencies:
                        inconsistencies[wine_type] = []
                    inconsistencies[wine_type].append(wine_id)
            else:
                type_food_mapping[wine_type] = food_ids

    if inconsistencies:
        print("Inconsistencies found in the following types:")
        for wine_type, ids in inconsistencies.items():
            print(f"Type: {wine_type}, IDs with inconsistencies: {', '.join(ids)}, Food IDs: {type_food_mapping[wine_type]}")
    else:
        print("All rows with the same type have the same food_ids.")



def extract_food_data():

    food_dict = {}

    with open("wine_data3.csv", mode='r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            food_ids = row['food_ids'].split(';')
            food_names = row['food_names'].split(';')

            for food_id, food_name in zip(food_ids, food_names):
                food_id = food_id.strip()
                food_name = food_name.strip()
                if food_id and food_name: 
                    food_dict[food_id] = food_name

    return food_dict


def index():
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')

    db = client['TasteBud']
    db.wines.create_index({
    "name": "text",
    "type": "text",
    "flavor_profile": "text"})
    print("Index created")
    
client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
db = client['TasteBud']

collection = db['wines']

index_name = 'default'
index_exists = False
for index in collection.list_indexes():
    if index['name'] == index_name:
        index_exists = True
        break

if index_exists:
    print(f"The '{index_name}' index exists in the collection.")
else:
    print(f"The '{index_name}' index does not exist in the collection.")