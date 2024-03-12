import csv
from pymongo import MongoClient

client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
db = client['TasteBud']
collection = db.Wines
input_csv_file = 'wine_data3.csv'

with open(input_csv_file, mode='r', newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    columns = reader.fieldnames[:15]  
    flavor_columns = ['flavor1', 'flavor2', 'flavor3', 'flavor4', 'flavor5']
    columns.append('review_count')
    columns.append('food_ids')

    for row in reader:
        wine_id = row['id']
        if collection.find_one({'_id': wine_id}):
            print(f"Wine with _id {wine_id} already exists in the database")
            continue  

        flavor_profile = [row.pop(flavor, None) for flavor in flavor_columns if flavor in columns]
        flavor_profile = [flavor for flavor in flavor_profile if flavor]

        food_ids = [int(food_id.strip()) for food_id in row['food_ids'].split(';') if food_id.strip().isdigit()]

        new_document = {key: row[key] for key in columns if key not in flavor_columns  and key != 'id'}
        new_document['flavor_profile'] = flavor_profile
        new_document['_id'] = wine_id
        new_document['food_id'] = food_ids

        for field in ['acidity', 'fizziness', 'intensity', 'sweetness', 'tannin', 'average_rating', 'price_amount', "review_count"]:
            if field in new_document:
                new_document[field] = float(row[field]) if row[field] not in ('N/A', '') else None

        collection.insert_one(new_document)
        print(f"Inserted wine with _id {wine_id} into the database")

print('Finished')