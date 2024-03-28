import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.cluster import KMeans
from pymongo import MongoClient

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

""" TODO : Will return the user's preferred wines as a dataframe, or the user's preferred
    flavors as a list
    Right now, just using hard-coded preferred wine_ids and flavors to test suggestions
"""
def get_user_prefs(db, user_id):
    collection = db.preferences
    query = {"user_id": user_id}
    cursor = collection.find_one(query)
    #df = pd.DataFrame(list(cursor))
    #df.set_index("_id", inplace=True)
    #return df

""" Creates KMeans clustering model based on numeric wine data
"""
def create_clusters(df_pref, wine_df, wine_numeric):
    x = wine_numeric.values
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    model = KMeans(n_clusters=6).fit(x_scaled)
    return model

""" Create suggestions for a user with >=1 wines marked as 'preferred'
    based on numerical features (intensity, sweetness, etc) and ideal price point
    @param pref_ids: a list of wine ids (str) marked as 'preferred' by the user
    @return suggestions: a list of wine ids (str) of length 5 to recommend to the user
"""
def suggest_wine_known_pref(db, pref_ids):
    wine_df = get_wine_df(db)
    df_pref = wine_df.loc[pref_ids]
    wine_numeric = wine_df.select_dtypes(include=np.number)
    wine_numeric = wine_numeric.fillna(wine_numeric.mean())
    wine_numeric.drop(['fizziness', 'review_count'], axis=1, inplace=True)
    averages = df_pref.mean(axis=0,skipna=True,numeric_only=True)
    averages.drop(['fizziness', 'review_count'], inplace=True)

    model = create_clusters(df_pref, wine_df, wine_numeric)
    wine_df['cluster'] = model.labels_
    wine_numeric['cluster'] = model.labels_
    dream_x = pd.DataFrame(averages.values.reshape(1,-1))
    results = model.predict(dream_x)
    our_cluster = wine_df.loc[wine_df['cluster']==results[0]]

    user_price = averages['price_amount']
    price_max = user_price + 20
    price_min = user_price - 20
    price_suggestions = our_cluster[(our_cluster['price_amount'] <= price_max) & (our_cluster['price_amount'] >= price_min)]

    suggestions = trim_suggestions(price_suggestions, df_pref, wine_df)
    suggestions = suggestions.index.to_list()
    print(suggestions)
    return suggestions

""" Takes initial list of suggestions, removing/adding wines to make it fit to 5 recommended
"""
def trim_suggestions(initial_suggestions, df_pref, wine_df):
    new_suggestions = pd.concat([initial_suggestions, df_pref])
    new_suggestions.drop_duplicates(subset=['name'], keep=False, inplace=True)
    if (len(new_suggestions.index) > 5):
        return new_suggestions.head(5)
    else:
        to_add = wine_df.head(5)
        new_suggestions = pd.concat([suggestions, to_add])
        return new_suggestions.head(5)
    return new_suggestions

""" Create suggestions for a new user who only has preferred flavors indicated
    @param pref_flavors: a list of flavors marked as preferred by user during intro quiz
    @return suggestions: a list of wine ids (str) of length 5 to recommend to the user
"""
def suggest_wine_generic(db, pref_flavors):
    wine_df = get_wine_df(db)
    flav_suggestions = pd.DataFrame().reindex_like(wine_df)
    for index, row in wine_df.iterrows():
        if any(flavor in row['flavor_profile'] for flavor in pref_flavors):
            flav_suggestions.loc[len(flav_suggestions.index)] = row
    flav_suggestions.dropna(subset=["name"], inplace=True)
    flav_suggestions.sort_values('price_amount', inplace=True)
    # for now, suggest the five cheapest options
    top_5 = flav_suggestions.head(5)
    suggestions = top_5.index.to_list()
    print(suggestions)
    return suggestions

""" Testing Method
"""
def test_suggestions(db):
    test_top_wines = ["1386686","5177761","1649800","8890662"]
    test_top_flavors = ["vanilla", "oak", "honey", "caramel"]
    suggest_wine_known_pref(db, test_top_wines) # test for 4 known preferred wines
    suggest_wine_generic(db, test_top_flavors) # test for 4 known preferred flavors (basic)

""" TODO : this is the method that will ultimately be called, but doesn't work/is unfinished until
           preferences table is initialized
    Call with a user's id (that links to the preferences collection) to get back a list of
    suggested wine_ids.
    @param user_id: the user_id that connects to the correct preferences document (w/ like_pref
    and flavor_pref arrays)
    @return suggestions: a list (length 5) of wine_ids suggested for the user
"""
def suggest_wines(user_id):
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
    db = client['TasteBud']

""" Just used for testing right now -->
"""
def main():
    print("hi")
    client = MongoClient('mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/')
    db = client['TasteBud']
    test_suggestions(db)

if __name__ == "__main__":
    main()