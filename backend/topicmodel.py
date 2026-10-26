import optuna
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


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

    def fit(self, X: np.ndarray):
        """Dummy function to avoid refitting"""
        pass

    def predict(self, X: np.ndarray):
        """Calls predict method of HDBSCAN"""
        predictions = self.model.predict(X)
        return predictions


class TopicModel:
    def __init__(
        self,
        min_cluster: int,
        max_cluster: int,
        embedding_model: SentenceTransformer = SentenceTransformer(EMBEDDING_MODEL),
        prob_threshold: float = 0.1,
        max_evals: int = 20,
        seed: int = 42423,
    ) -> None:
        """Initializes the TopicModel class

        Args:
          min_cluster (int): the minimum number of clusters, if cluster solution is below this number, a penalty is applied
          max_cluster (int): the maximum number of clusters, if cluster solution is above this number, a penalty is applied
          prob_threshold (float): the probability threshold for the cluster
          max_evals (int): the maximum number of evaluations for hyperparameter optimization
          seed (int): random seed

        Returns:
          None
        """

        assert min_cluster < max_cluster, "min_cluster must be smaller than max_cluster"
        assert (
            prob_threshold > 0.0 and prob_threshold < 1.0
        ), "prob_threshold must be between 0.0 and 1.0"
        assert max_evals > 0, "max_evals must be greater than 0"
        assert seed > 0, "seed must be greater than 0"

        self.docs = None
        self._embedding_model = embedding_model
        self.embeddings = None
        self.embeddings2d = None
        self.best_model = {"cost": None, "ntopics": None, "umap": None, "cluster": None}
        self.min_cluster = min_cluster
        self.max_cluster = max_cluster
        self.prob_threshold = prob_threshold
        self.max_evals = max_evals
        self.seed = seed

    def embed_docs(self, docs: list[str]) -> None:
        """Embeds the documents

        Args:
            docs (list[str]): list of documents

        Returns:
            None
        """
        self.docs = docs
        self.embeddings = self._embedding_model.encode(docs)

    def _is_better_model(self, cost: float) -> bool:
        """Compare the cost of the model to the best model so far

        Args:
            cost (float): return value of `_compute_cost`

        Returns:
            bool: `True` if the cost is lower than the best model so far, `False` otherwise
        """
        if self.best_model["cost"] is None:
            return True
        else:
            return cost < self.best_model["cost"]

    def _set_best_model(
        self, cost: float, ntopics: int, umap: UMAP, cluster: HDBSCAN
    ) -> None:
        """Updates best model

        Args:
            cost (float): cost of the model
            ntopics (int): number of topics found
            umap (UMAP): umap model
            cluster (HDBSCAN): hdbscan model

        Returns:
            None
        """
        self.best_model["cost"] = cost
        self.best_model["ntopics"] = ntopics
        self.best_model["umap"] = umap
        self.best_model["cluster"] = cluster

    def _compute_cost(
        self, clusters: HDBSCAN, out_of_range_cluster_penalty: float = 0.15
    ) -> tuple[int, float]:
        """Computes the cost function for the model

        Implementation from https://github.com/dborrelli/chat-intents/blob/main/chatintents/chatintents.py, 
        original idea from Nikolay Oskolkov (https://towardsdatascience.com/how-to-cluster-in-high-dimensions-4ef693bacc6/).

        Args:
            clusters (HDBSCAN): fitted hdbscan model
            out_of_range_cluster_penalty (float, optional): the penalty for the number of clusters outside the desired range. Defaults to 0.15.

        Returns:
            tuple[int, float]: number of topics and cost
        """
        cluster_labels = clusters.labels_
        label_count = len(np.unique(cluster_labels)) - 1
        total_num = len(clusters.labels_)
        cost = (
            np.count_nonzero(clusters.probabilities_ < self.prob_threshold) / total_num
        )

        # penalty on the cost function if outside the desired range
        # for the number of clusters
        if (label_count < self.min_cluster) | (label_count > self.max_cluster):
            penalty = out_of_range_cluster_penalty
        else:
            penalty = 0.0

        cost = cost + penalty

        return label_count, cost

    def _objective(self, trial: optuna.trial.Trial, X: np.ndarray) -> float:
        """Compute

        Args:
            trial (optuna.trial.Trial): optuna trial object
            X (np.ndarray): raw embeddings

        Returns:
            float: the cost of the model
        """
        # search space
        n_neighbors = trial.suggest_int("n_neighbors", 4, 12)
        n_components = trial.suggest_int("n_components", 3, 12)
        min_cluster_size = trial.suggest_int("min_cluster_size", 5, 15)
        min_samples = trial.suggest_int("min_samples", 2, 4)

        # setup models
        dim_reducer = UMAP(
            n_neighbors=n_neighbors,
            n_components=n_components,
            metric="cosine",
            random_state=self.seed,
        )
        cluster = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)

        # fit model
        dim_reducer.fit(X)
        reduced_embeddings = dim_reducer.transform(X)
        cluster.fit_predict(reduced_embeddings)

        label_count, cost = self._compute_cost(cluster, 0.15)

        if self._is_better_model(cost):
            self._set_best_model(cost, label_count, dim_reducer, cluster)

        return cost

    def optimize_umap_hdbscan(self) -> dict:
        """
        Optimizes the UMAP and HDBSCAN parameters using Optuna library.

        UMAP: n_neighbors, n_components
        HDBSCAN: min_cluster_size, min_samples

        Raises:
            ValueError: If embeddings are not found. You must first call embed_docs method.

        Returns:
            A dictionary containing the best parameters found by Optuna for UMAP and HDBSCAN.
            The dictionary contains the following keys:
                - n_neighbors: int
                - n_components: int
                - min_cluster_size: int
                - min_samples: int
        """
        if not self.embeddings:
            raise ValueError(
                "Embeddings not found, you must first call embed_docs method."
            )

        study = optuna.create_study(
            direction="minimize", sampler=optuna.samplers.TPESampler(seed=self.seed)
        )
        study.optimize(
            lambda trial: self._objective(trial, self.embeddings),
            n_trials=self.max_evals,
        )
        return study.best_params

    def _compute_2d_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Computes the 2d embeddings for visualization

        Args:
            embeddings (np.ndarray): raw embeddings

        Returns:
            np.ndarray: 2d embeddings
        """
        if not self.best_model["umap"]:
            raise ValueError("UMAP model not found, you must first call optim method.")
        n_neighbors = self.best_model["umap"].n_neighbors
        umap2d = UMAP(
            n_neighbors=n_neighbors,
            n_components=2,
            metric="cosine",
            random_state=self.seed,
        )
        umap2d.fit(embeddings)
        self.embeddings2d = umap2d.transform(embeddings)

    def get_labels(self) -> np.ndarray:
        """Returns the labels for the best model

        Returns:
          labels (np.ndarray): the labels for the best model
        """
        if not self.best_model["cluster"]:
            raise ValueError("Best model not found, you must first call optim method.")
        return self.best_model["cluster"].labels_


if __name__ == "__main__":
    from sklearn.datasets import fetch_20newsgroups
    from umap import UMAP
    from sentence_transformers import SentenceTransformer

    newsgroups_train = fetch_20newsgroups(subset="train")

    # only keep computer related topics
    comp_docs = []
    targets = []
    for doc, target in zip(newsgroups_train.data, newsgroups_train.target):
        if newsgroups_train.target_names[target].startswith("comp"):
            comp_docs.append(doc)
            targets.append(target)

    model = TopicModel()
    model.embed_docs(comp_docs)
    best_params = model.optimize_umap_hdbscan()
    print(
        f"\n\n #### BEST PARAMETERS ({model.best_model['ntopics']} clusters):\n {best_params}"
    )

    unique_labels = np.unique(targets)
    print(f"\n\n #### TRUE LABELS:\n {len(unique_labels)}")
