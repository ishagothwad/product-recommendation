import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# =========================
# LOAD DATA
# =========================

DATA_PATH = "marketing_sample_for_walmart_com-walmart_com_product_review__20200701_20201231__5k_data.tsv"

train_data = pd.read_csv(DATA_PATH, sep="\t")

# Select useful columns
train_data = train_data[
    [
        "Uniq Id",
        "Product Id",
        "Product Rating",
        "Product Reviews Count",
        "Product Category",
        "Product Brand",
        "Product Name",
        "Product Image Url",
        "Product Description",
        "Product Tags",
    ]
]

# Rename columns
train_data.rename(
    columns={
        "Uniq Id": "ID",
        "Product Id": "ProdID",
        "Product Rating": "Rating",
        "Product Reviews Count": "ReviewCount",
        "Product Category": "Category",
        "Product Brand": "Brand",
        "Product Name": "Name",
        "Product Image Url": "ImageURL",
        "Product Description": "Description",
        "Product Tags": "Tags",
    },
    inplace=True,
)

train_data.dropna(subset=["Name", "Description"], inplace=True)

# =========================
# NLP CLEANING
# =========================

nlp = spacy.load("en_core_web_sm")

def clean_and_extract_tags(text):
    doc = nlp(str(text).lower())
    tokens = [
        token.text
        for token in doc
        if token.text.isalnum() and token.text not in STOP_WORDS
    ]
    return " ".join(tokens)

for col in ["Category", "Brand", "Description"]:
    train_data[col] = train_data[col].apply(clean_and_extract_tags)

# Create combined tags column
train_data["Tags"] = (
    train_data["Category"]
    + " "
    + train_data["Brand"]
    + " "
    + train_data["Description"]
)

# =========================
# TF-IDF MODEL (BUILT ONCE)
# =========================

tfidf_vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf_vectorizer.fit_transform(train_data["Tags"])
cosine_sim_matrix = cosine_similarity(tfidf_matrix)

# =========================
# CONTENT-BASED RECOMMENDER
# =========================

def content_based_recommendations(data, item_name, top_n=8):
    if item_name not in data["Name"].values:
        return None

    idx = data[data["Name"] == item_name].index[0]

    similarity_scores = list(enumerate(cosine_sim_matrix[idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    top_items = similarity_scores[1 : top_n + 1]
    item_indices = [i[0] for i in top_items]

    return data.iloc[item_indices][
        ["Name", "ReviewCount", "Brand", "ImageURL", "Rating"]
    ]

# =========================
# COLLABORATIVE FILTERING
# =========================

def collaborative_filtering_recommendations(data, target_user_id, top_n=10):
    user_item_matrix = (
        data.pivot_table(
            index="ID", columns="ProdID", values="Rating", aggfunc="mean"
        )
        .fillna(0)
    )

    if target_user_id not in user_item_matrix.index:
        return None

    user_similarity = cosine_similarity(user_item_matrix)
    target_index = user_item_matrix.index.get_loc(target_user_id)

    similarity_scores = user_similarity[target_index]
    similar_users = similarity_scores.argsort()[::-1][1:]

    recommended_items = []

    for user_idx in similar_users:
        rated = user_item_matrix.iloc[user_idx]
        not_rated = (rated > 0) & (user_item_matrix.iloc[target_index] == 0)
        recommended_items.extend(user_item_matrix.columns[not_rated])

    recommended_items = list(set(recommended_items))

    return data[data["ProdID"].isin(recommended_items)][
        ["Name", "ReviewCount", "Brand", "ImageURL", "Rating"]
    ].head(top_n)

# =========================
# HYBRID RECOMMENDATION
# =========================

def hybrid_recommendations(data, target_user_id, item_name, top_n=10):
    content_rec = content_based_recommendations(data, item_name, top_n)
    collab_rec = collaborative_filtering_recommendations(data, target_user_id, top_n)

    if content_rec is None and collab_rec is None:
        return None
    elif content_rec is None:
        return collab_rec
    elif collab_rec is None:
        return content_rec

    hybrid = pd.concat([content_rec, collab_rec]).drop_duplicates()
    return hybrid.head(top_n)

