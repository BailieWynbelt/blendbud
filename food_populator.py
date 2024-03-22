
from pymongo import MongoClient
food_name  = {'4': 'Beef', '8': 'Lamb', '11': 'Game (deer, venison)', '20': 'Poultry', '10': 'Pork', '13': 'Shellfish', '19': 'Vegetarian', '39': 'Goat cheese', '9': 'Veal', '12': 'Rich fish (salmon, tuna etc)', '35': 'Mild and soft cheese', '0': 'N/A', '27': 'Appetizers and snacks', '28': 'Lean fish', '41': 'Cured Meat', '5': 'Pasta', '17': 'Mature and hard cheese', '16': 'Sweet desserts', '38': 'Blue cheese', '40': 'Aperitif', '15': 'Spicy food', '34': 'Mushrooms', '37': 'Fruity desserts'}
food_pair  = food_wine_pairings = {
    'Beef': 'Rich, full-bodied red wines like Cabernet Sauvignon or Malbec complement beef by balancing its robust flavors and high fat content with strong tannins and deep, complex flavors.',
    'Lamb': 'Medium to full-bodied red wines with good acidity, such as Shiraz or Bordeaux blends, enhance lamb’s rich, slightly gamey flavors with their structured tannins and spicy notes.',
    'Game (deer, venison)': 'Complex, full-bodied red wines like Barolo or Zinfandel pair well with game meats, complementing their intense flavors and textures with high tannins and rich, earthy notes.',
    'Poultry': 'White wines like Chardonnay or light to medium-bodied reds such as Pinot Noir work well with poultry by matching its lighter flavors and textures with subtle fruitiness and balanced acidity.',
    'Pork': 'Light reds like Pinot Noir or richer whites like Viognier bring out the flavors in pork, with the wines’ fruity and slightly acidic profiles cutting through the fat and enhancing the meat’s natural flavors.',
    'Shellfish': 'Crisp, acidic white wines like Sauvignon Blanc or Champagne cleanse the palate and highlight the delicate flavors of shellfish with their zesty acidity and fresh, mineral notes.',
    'Vegetarian': 'Light, aromatic whites like Riesling or Grüner Veltliner pair well with vegetarian dishes, enhancing the freshness of the vegetables and complementing the variety of flavors with their fruity and floral notes.',
    'Goat cheese': 'Acidic white wines like Chenin Blanc or Sauvignon Blanc cut through the tanginess of goat cheese, balancing its creamy texture with crisp, refreshing acidity.',
    'Veal': 'Light to medium-bodied wines, such as Chardonnay or lighter styles of Merlot, complement veal’s delicate flavors with their subtle fruit notes and balanced structure.',
    'Rich fish (salmon, tuna etc)': 'Full-bodied white wines like oaked Chardonnay or robust rosés balance the oily richness of fish like salmon and tuna, offering a counterpoint to the fattiness with rich, buttery, and complex flavors.',
    'Mild and soft cheese': 'Light-bodied white wines like Pinot Grigio complement mild and soft cheeses by providing a delicate, refreshing acidity that cleanses the palate without overpowering the cheese’s subtle flavors.',
    'N/A': 'Depends on the specific characteristics of the food or context, aiming to create a harmonious balance between the food’s flavors and the wine’s profile.',
    'Appetizers and snacks': 'Sparkling wines like Prosecco or light whites such as Sauvignon Blanc are versatile, providing a refreshing and palate-cleansing effect that complements a wide range of flavors in various appetizers and snacks.',
    'Lean fish': 'Light, citrusy white wines like Albariño or Pinot Gris enhance the delicate flavors of lean fish, matching their lightness with bright acidity and subtle fruity or floral notes.',
    'Cured Meat': 'Wines with good acidity and fruitiness, such as Tempranillo or Sangiovese, complement cured meats by balancing the saltiness and intensity with juicy fruit flavors and a refreshing acidity.',
    'Pasta': 'The wine pairing for pasta varies with the sauce; acidic reds like Chianti are perfect for tomato-based sauces, providing a balance to the acidity of the tomatoes, while full-bodied whites like Chardonnay enhance cream-based sauces with their rich, buttery textures.',
    'Mature and hard cheese': 'Full-bodied red wines like Cabernet Sauvignon or aged whites like vintage Chardonnay pair well with mature and hard cheeses, matching their intense flavors and rich textures with equally robust and complex wine profiles.',
    'Sweet desserts': 'Sweet wines like Moscato d’Asti or Port complement sweet desserts by echoing their sweetness, adding depth with their own flavors and providing a pleasing contrast to the dessert’s richness.',
    'Blue cheese': 'The strong, pungent flavors of blue cheese are well matched with the sweet and often botrytized wines like Sauternes or aromatic and intense wines like Gewürztraminer, balancing the cheese’s sharpness with sweetness or aromatic intensity.',
    'Aperitif': 'Light and refreshing wines like dry sparkling wines or crisp whites such as Champagne or Aperitif wines stimulate the appetite and prepare the palate for a meal, offering a refreshing start that complements a variety of opening courses or appetizers.',
    'Spicy food': 'Off-dry whites like Riesling or Gewürztraminer with their sweetness and acidity can cool the heat of spicy foods, balancing the spiciness with their fruity sweetness and crisp acidity.',
    'Mushrooms': 'Earthy red wines like Pinot Noir or Gamay complement mushrooms, enhancing their umami flavors with the wines’ own earthy, forest-floor characteristics and subtle tannins.',
    'Fruity desserts': 'Light and slightly sweet or fruity wines, such as Rosé or a light red like Schiava, complement fruity desserts by enhancing the fruit flavors without overwhelming the dessert’s sweetness.'
}


combined_data = [
    {'_id': int(food_id), 'food_name': food_name, 'description': food_pair[food_name]}
    for food_id, food_name in food_name.items()
    if food_name in food_pair
]

client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
db = client['TasteBud']
food_collection = db['food']

food_collection.insert_many(combined_data)

print('Data inserted')