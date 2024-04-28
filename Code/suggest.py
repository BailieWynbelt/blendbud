import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.cluster import KMeans
from pymongo import MongoClient


##########################################################################


""" Returns the wine collection as a pandas df
    @return df: pandas df of wines with _id number as the index
"""
def get_wine_df(db):
    collection = db.wines
    query = {}
    cursor = collection.find(query)
    df = pd.DataFrame(list(cursor))
    df.set_index("_id", inplace=True)
    return df

""" Trims or adds to list of suggestions to make it contain exactly 5 wines
"""
def trim_suggestions(initial_suggestions, df_pref, wine_df):
    new_suggestions = pd.concat([initial_suggestions, df_pref])
    new_suggestions.drop_duplicates(subset=['name'], keep=False, inplace=True)
    if (len(new_suggestions.index) > 5):
        return new_suggestions.sample(5)
    else:
        to_add = wine_df.head(5)
        new_suggestions = pd.concat([initial_suggestions, to_add])
        return new_suggestions.sample(5)
    return new_suggestions

""" Creates KMeans clustering model (n=6) based on the numeric columns of wine data
"""
def create_clusters(df_pref, wine_df, wine_numeric):
    x = wine_numeric.values
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    model = KMeans(n_clusters=6).fit(x_scaled)
    return model


##########################################################################


""" Create suggestions for a user with >=1 wines marked as 'preferred'
    based on numerical features (intensity, sweetness, etc) and ideal price point
    @param pref_ids: a list of wine ids (str) marked as 'preferred' by the user
    @return suggestions: a list of wine ids (str) of length 5 to recommend to the user
"""
def suggest_wine_known_pref(wine_df, pref_ids):
    df_pref = wine_df.loc[pref_ids]
    wine_numeric = wine_df.select_dtypes(include=np.number)
    wine_numeric = wine_numeric.fillna(wine_numeric.mean())
    wine_numeric.drop(['fizziness', 'review_count', 'tannin'], axis=1, inplace=True)
    averages = df_pref.mean(axis=0,skipna=True,numeric_only=True)
    averages.drop(['fizziness', 'review_count', 'tannin'], inplace=True)

    # Creating the clustering model:
    model = create_clusters(df_pref, wine_df, wine_numeric)
    wine_df['cluster'] = model.labels_
    wine_numeric['cluster'] = model.labels_
    dream_x = pd.DataFrame(averages.values.reshape(1,-1))
    results = model.predict(dream_x)
    our_cluster = wine_df.loc[wine_df['cluster']==results[0]]

    # Narrowing down the suggestions by ideal user price and trimming/adding to suggest only 5 wines:
    user_price = averages['price_amount']
    price_max = user_price + 20
    price_min = user_price - 20
    price_suggestions = our_cluster[(our_cluster['price_amount'] <= price_max) & (our_cluster['price_amount'] >= price_min)]
    suggestions = trim_suggestions(price_suggestions, df_pref, wine_df)
    suggestions = suggestions.index.to_list()
    print("known", suggestions)
    return suggestions

""" Create suggestions for a new user who only has preferred flavors indicated
    @param pref_flavors: a list of flavors marked as preferred by user during intro quiz
    @return suggestions: a list of wine ids (str) of length 5 to recommend to the user
"""
def suggest_wine_generic(wine_df, pref_flavors):
    # Get wines that have flavors matching our user's top flavor:
    print("pref flavors:", pref_flavors)
    flav_suggestions = []
    for index, row in wine_df.iterrows():
        if any(flavor in row['flavor_profile'] for flavor in pref_flavors):
            flav_suggestions.append(index)
    suggestions = flav_suggestions[:5]
    print("generic", suggestions)
    return suggestions

""" Backup method to provide 5 suggestions for the cheapest highest-rated wines
    @return suggestions: /currently/ a mongodb cursor with 5 wine records
"""
def suggest_failsafe_wines():
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
    db = client['TasteBud']
    wine_collection = db.wines
    top_wines = wine_collection.find().sort("average_rating", -1).limit(20)
    cheap_top_wines = top_wines.sort("price_amount").limit(5)
    suggestions = []
    for wine in cheap_top_wines:
        suggestions.append(wine["_id"])
    return suggestions

""" Creates wine suggestions for two users based on their wine and flavor preferences
    @param like_pref1, flav_pref1: preferences arrays from user1
            like_pref2, flav_pref2: preferences arrays from user2
    @return suggestions: a list of wine ids (str) of length 5 to recommend as a blend
"""
def suggest_wine_blend(like_pref1, flav_pref1, like_pref2, flav_pref2):
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
    db = client['TasteBud']
    wine_df = get_wine_df(db)
    # Combining the two users' likes/flavors preferences and deciding to suggest based on wine or flavor:
    like_pref = like_pref1 + like_pref2
    flav_pref = flav_pref1 + flav_pref2
    print("like_pref:", like_pref)
    print("flav_pref:", flav_pref)
    if len(like_pref) > 0:
        print("suggesting based on known liked wines")
        return suggest_wine_known_pref(wine_df, like_pref)
    elif len(like_pref) == 0:
        print("suggesting based on flavors")
        return suggest_wine_generic(wine_df, flav_pref)
    print("returning failsafe wines")
    return suggest_failsafe_wines

""" Get wine suggestions for a user based on past wines they liked (if available), or flavors they
    have marked as liked.
    @param indicator: a string ("like"/"flavor") indicating which list from the user's pref is being sent
           pref_list: an array from the user's preferences (see note below)
    @return suggestions: a list (length 5) of wine_ids suggested for the user
    NOTE Call with string indicating (like/flavor) and corresponding list to use
    (If the like_pref list is empty, use the flavor_pref list. Even if flavor_pref is empty,
    there will be a failsafe method implemented)
"""
def suggest_wines(indicator, pref_list):
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
    db = client['TasteBud']
    wine_df = get_wine_df(db)
    if indicator == "like":
        return suggest_wine_known_pref(wine_df, pref_list)
    elif indicator == "flavor":
        if len(pref_list) == 0:
            return suggest_failsafe_wines()
        return suggest_wine_generic(wine_df, pref_list)
    return suggest_failsafe_wines()


##########################################################################


""" Testing Method
"""
def test_suggestions(wine_df):
    test_top_wines = ["1386686","5177761","1649800","8890662"]
    test_top_flavors = ["vanilla", "oak", "honey", "caramel"]
    suggest_wine_known_pref(wine_df, test_top_wines) # test for 4 known preferred wines
    suggest_wine_generic(wine_df, test_top_flavors) # test for 4 known preferred flavors (basic)

""" Just used for testing  -->
"""
#def main():
#    print("hi")
#    print(suggest_failsafe_wines())
#    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
#    db = client['TasteBud']
#    wine_df = get_wine_df(db)
#    test_suggestions(wine_df)

#if __name__ == "__main__":
#    main()