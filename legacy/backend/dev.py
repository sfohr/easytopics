from umap import UMAP
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
import pandas as pd
from bertopic import BERTopic
from bertopic.cluster import BaseCluster
from bertopic.representation import KeyBERTInspired
from sklearn.feature_extraction.text import CountVectorizer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
df = pd.read_csv("./backend/20newsgroup_data_comp_20perCl.csv", sep=";")
documents = df["text"].tolist()
embeddings = embedder.encode(documents, show_progress_bar=True)
umap = UMAP(n_neighbors=15, n_components=5, metric="cosine", random_state=42)
hdbscan = HDBSCAN(min_cluster_size=5, min_samples=2)

# fit model
umap.fit(embeddings)
reduced_embeddings = umap.transform(embeddings)
hdbscan.fit(reduced_embeddings)


class UMAPWrapper:
    """Wrapper for UMAP to avoid refitting in BERTopic"""

    def __init__(self, fitted_model: UMAP):
        """Initializes the wrapper

        Args:
            fitted_model (UMAP): A fitted UMAP model
        """
        self.model = fitted_model

    def fit(self, X) -> None:
        """Dummy function to avoid refitting"""
        pass

    def transform(self, X):
        """Calls transform method of UMAP"""
        embeddings = self.model.transform(X)
        return embeddings


class HDBSCANWrapper:
    """Wrapper for HDBSCAN to avoid refitting in BERTopic"""

    def __init__(self, fitted_model: HDBSCAN):
        """Initializes the wrapper

        Args:
            fitted_model (HDBSCAN): A fitted HDBSCAN model
        """
        self.model = fitted_model
        self.labels_ = fitted_model.labels_

    def fit(self, X):
        """Dummy function to avoid refitting"""
        pass

    def predict(self, X):
        """Calls predict method of HDBSCAN"""
        predictions = self.model.predict(X)
        return predictions


empty_cluster_model = BaseCluster()
vectorizer_model = CountVectorizer(min_df=0.007, max_df=0.7)
representation_model = KeyBERTInspired(random_state=42)
topics = hdbscan.labels_

tm = BERTopic(
    embedding_model=embedder,
    umap_model=UMAPWrapper(umap),
    hdbscan_model=HDBSCANWrapper(hdbscan),
    vectorizer_model=vectorizer_model,
    representation_model=representation_model,
    calculate_probabilities=False,
    verbose=True,
)
tm.fit(documents, embeddings=embeddings)

document_df = tm.get_document_info(documents)
document_df.to_csv("./backend/test_test_test.csv", sep=";")

print("done")
