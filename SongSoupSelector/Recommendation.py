import tkinter

import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist

pd.options.mode.chained_assignment = None


def cosine_sim(v1, v2):
    distance = cdist(v1, v2, 'cosine')
    return distance
    # return sum(dot(v1, v2) / (norm(v1) * norm(v2)))


def collect_content(dataframe: pd.DataFrame):
    import re
    dataframe["content"] = dataframe.apply(
        lambda x:
        f'{" ".join([x["primary_artist"].lower().replace(" ", "")] * (1 if x["track_genre"] else 2))} '
        # f'{" ".join([x["primary_artist_id"].replace(" ", "")] * (20 if x["primary_artist_id"] else 2))} '
        f'{" ".join([" ".join(x["secondary_artists"].lower().split(","))] * (10 if x["secondary_artists"] else 0))} '
        # f'{" ".join([x["secondary_artist_ids"]] * (13 if x["secondary_artist_ids"] else 0))} '
        f'{" ".join([x["name"].lower()] * (1 if x["track_genre"] else 2))} '
        # f'{" ".join([x["album"].lower()] * (1 if x["album"] else 0))} '
        # f'{" ".join([x["album_id"].lower()] * (6 if x["album_id"] else 0))} '
        f'{" ".join([x["track_genre"]] * (3 if x["track_genre"] else 0))} '
        f'{" ".join([x["time_signature"]] * (1 if x["time_signature"] != "nantsig" else 0))} ',
        # f'{" ".join([x["cluster_label"]] * 1)}',
        axis=1,
    )

    dataframe["content"] = dataframe["content"].apply(
        lambda x: re.sub(r'[^\w\s]', '', x)
    )


class Recommendation:
    def __init__(self, df: pd.DataFrame, status: tkinter.Label, progress: tkinter.ttk.Progressbar, ids=None, name=None):
        self.df = df[:]
        if ids:
            self.id = list(set(ids))
            self.provided_songs_df = self.df[self.df.index.isin(self.id)]
        elif name:
            pass

        self.decades = self.provided_songs_df["decade"].unique()
        self.clusters = self.provided_songs_df["cluster_label"].unique()

        self.song_index = None

        self.df['secondary_artists'].fillna("", inplace=True)
        self.df['track_genre'].fillna("", inplace=True)

        self.pa = list(self.provided_songs_df['primary_artist'])
        self.name = list(self.provided_songs_df['name'])
        print(f"Recommending songs similar to {self.name} by {self.pa}\nDataset shape: {self.df.shape}")

        self.status = status
        self.progress = progress

    def recommend(
            self, max_songs=10, dist_factor=0.9, find_other_artists=False, simple=True, same_decade=True, use_tfidf=0
    ):

        self.df = self.df[(self.df["track_genre"].isin(set(self.provided_songs_df["track_genre"].values))) & (self.df["cluster_label"].isin(self.clusters))]

        if same_decade:
            self.df = self.df[self.df["decade"].isin(self.decades)]

        print(self.decades)

        # Making calculations based on numeric features
        df_num = self.df.select_dtypes([np.number])
        df_num.drop("decade", inplace=True, axis=1)
        input_vec = [np.average([df_num[df_num.index.isin([i])].values.flatten() for i in self.id], axis=0)]

        self.status.config(text="Calculating song metrics")
        self.progress.step(33.3)
        self.status.update_idletasks()

        input_vec = np.array(input_vec)

        distances = cosine_sim(input_vec, np.array(df_num))
        indices = np.argsort(distances)[:, :min(5000, self.df.shape[0]) + len(self.id)]
        ranks = np.argsort(indices)
        ranks = pd.DataFrame(ranks.reshape(-1, 1), columns=["rank"])

        rec_songs = self.df.iloc[indices[0]]

        self.df = rec_songs

        self.df.reset_index(inplace=True, names="id")
        self.df.insert(len(self.df.columns), "dist_rank", -1)
        self.df["dist_rank"] = ranks["rank"]

        collect_content(self.provided_songs_df)
        collect_content(self.df)

        song_ids = self.df.index.to_series()
        idx = pd.Series(self.df["id"], index=song_ids)
        self.song_index = list(idx[idx.isin(self.id)].index)

        self.status.config(text="Observing categorical content.\nCan take a while")
        self.progress.step(33.3)
        self.status.update_idletasks()

        if use_tfidf:
            count = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                min_df=0.0,
            )
        else:
            count = CountVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                min_df=0.0,
                stop_words="english",
            )
        self.provided_songs_df.reset_index(inplace=True, names="id")
        df_appended = self.provided_songs_df._append(self.df)
        self.df = df_appended.drop_duplicates(subset=["id"], keep="first")

        self.df.insert(len(self.df.columns) - 1, "categorical_similarity", 0)
        count_matrix = count.fit_transform(self.df["content"])
        csim_cv = cosine_similarity(count_matrix, count_matrix)

        for ind, row in self.df.iterrows():
            for x in range(self.provided_songs_df.shape[0]):
                self.df["categorical_similarity"][ind] += csim_cv[ind][x]

        self.df['categorical_similarity'] = self.df['categorical_similarity'].apply(lambda x: x / self.provided_songs_df.shape[0])

        indices_cat = np.argsort(self.df['categorical_similarity'].values)[::-1]
        ranks_cat = np.argsort(indices_cat)
        ranks_cat = pd.DataFrame(ranks_cat.reshape(-1, 1), columns=["rank"])

        self.df = self.df.iloc[indices_cat[:]]
        self.df.insert(len(self.df.columns), "cat_rank", -1)
        self.df["cat_rank"] = ranks_cat["rank"]

        self.status.config(text="Hang in there, we're almost done!")
        self.progress.step(33.3)
        self.status.update_idletasks()

        self.df["overall_proximity"] = self.df.apply(lambda x: (x["dist_rank"] * dist_factor) + (x["cat_rank"] * (1 - dist_factor)), axis=1)

        # All calculations involving vectors should be complete at this point
        if find_other_artists:
            self.df = self.df[~self.df['primary_artist'].isin(self.pa)].nsmallest(columns="overall_proximity", n=max_songs + len(self.id))
        else:
            self.df = self.df.nsmallest(columns="overall_proximity", n=max_songs + len(self.id))

        self.df.drop('content', axis=1, inplace=True)

        self.df = self.df[~self.df['id'].isin(self.id)]

        self.df.reset_index(inplace=True, drop=True)
        self.progress.step(0.1)
        self.status.config(text="See anything interesting? Try again?")
        if simple:

            self.df.rename(columns={"name": "Song", "track_genre":"Genre", "release_date":"Released"}, inplace=True)
            self.df['Artists'] = self.df.apply(
                lambda x: x['primary_artist'] + ('with ' + x['secondary_artists'] if x['secondary_artists'] else '')
            , axis=1)
            # return self.df[['name', 'primary_artist', 'secondary_artists', 'track_genre']
            return self.df[['Released','Song', 'Artists', 'Genre']]
        else:
            return self.df
            # return self.df[['name', 'primary_artist', 'secondary_artists', 'track_genre', 'id', 'overall_proximity', 'dist_rank', 'cat_rank']]
