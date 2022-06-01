import random
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# https://towardsdatascience.com/implementing-a-decision-tree-from-scratch-f5358ff9c4bb

# RandomForest Predict/Fit methods and Classification report in courtesy of Ying Kang

class Node:
    def __init__(self, feature=None, threshold=None, left=None, right=None, *, value=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    def is_leaf(self):
        return self.value is not None


class DecisionTreeModel:

    def __init__(self, max_depth=100, criterion='gini', min_samples_split=2, impurity_stopping_threshold=0):
        self.max_depth = max_depth
        self.criterion = criterion
        self.min_samples_split = min_samples_split
        self.impurity_stopping_threshold = impurity_stopping_threshold
        self.root = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        # call the _fit method
        self._fit(X.to_numpy(), y.to_numpy())
        print("Done fitting")

    def predict(self, X: pd.DataFrame):
        # call the predict method
        return self._predict(X.to_numpy())

    def _fit(self, X, y):
        self.root = self._build_tree(X, y)

    def _predict(self, X):
        predictions = [self._traverse_tree(x, self.root) for x in X]
        return np.array(predictions)

    def _is_finished(self, y, depth):
        # modify the signature of the method if needed
        if (depth >= self.max_depth
                or self.n_class_labels == 1
                or self.n_samples < self.min_samples_split
                or self._is_homogenous_enough(y)):
            return True
        return False

    def _is_homogenous_enough(self, y):
        result = False
        if self.criterion == "gini":
            loss = self._gini(y)
        else:
            loss = self._entropy(y)

        if loss < self.impurity_stopping_threshold:
            result = True

        return result

    def _build_tree(self, X, y, depth=0):
        self.n_samples, self.n_features = X.shape
        self.n_class_labels = len(np.unique(y))

        # stopping criteria
        if self._is_finished(y, depth):
            u, counts = np.unique(y, return_counts=True)
            most_common_Label = u[np.argmax(counts)]
            return Node(value=most_common_Label)

        # get best split
        rnd_feats = np.random.choice(self.n_features, self.n_features, replace=False)
        best_feat, best_thresh = self._best_split(X, y, rnd_feats)

        # grow children recursively
        left_idx, right_idx = self._create_split(X[:, best_feat], best_thresh)
        left_child = self._build_tree(X[left_idx, :], y[left_idx], depth + 1)
        right_child = self._build_tree(X[right_idx, :], y[right_idx], depth + 1)
        return Node(best_feat, best_thresh, left_child, right_child)

    def _gini(self, y):
        '''
        For the gini method, the formula for gini_index is provided with dummy encoding just in case we deal with
        categorical variables
        '''
        u, counts = np.unique(y, return_counts=True)
        proportions = counts / len(y)
        gini = np.sum([p * (1 - p) for p in proportions if p > 0])

        return gini

    def _entropy(self, y):
        # proportions is another word for probability
        u, counts = np.unique(y, return_counts=True)
        proportions = counts / len(y)
        entropy = -np.sum([p * np.log2(p) for p in proportions if p > 0])

        return entropy

    def _create_split(self, X, thresh):
        left_idx = np.argwhere(X <= thresh).flatten()
        right_idx = np.argwhere(X > thresh).flatten()
        return left_idx, right_idx

    def _information_gain(self, X, y, thresh):
        '''
        Depending on the criterion of the decision tree model, the parent loss and child loss will rely on either
        gini or entropy
        '''

        if self.criterion == 'gini':
            parent_loss = self._gini(y)
        else:
            parent_loss = self._entropy(y)

        left_idx, right_idx = self._create_split(X, thresh)
        n, n_left, n_right = len(y), len(left_idx), len(right_idx)

        if n_left == 0 or n_right == 0:
            return 0

        if self.criterion == 'gini':
            child_loss = (n_left / n) * self._gini(y[left_idx]) + (n_right / n) * self._gini(y[right_idx])
        else:
            child_loss = (n_left / n) * self._entropy(y[left_idx]) + (n_right / n) * self._entropy(y[right_idx])

        return parent_loss - child_loss

    def _best_split(self, X, y, features):
        '''
         We loop through all the feature indices and unique threshold values to calculate the information gain
         If we find a better split we store the associated parameters.
         After going through all the traversals, we return the best feat and threshold
        '''
        split = {'score': - 1, 'feat': None, 'thresh': None}

        for feat in features:
            X_feat = X[:, feat]
            thresholds = np.unique(X_feat)
            for thresh in thresholds:
                score = self._information_gain(X_feat, y, thresh)

                if score > split['score']:
                    split['score'] = score
                    split['feat'] = feat
                    split['thresh'] = thresh

        return split['feat'], split['thresh']

    def _traverse_tree(self, x, node):
        '''
        Recursively traverse the tree in order to get our predictions
        Compare the node feature and threshold values to the current sample’s values and decide the direction based on
        if the threshold is bigger or equal to the feature
        '''
        if node.is_leaf():
            return node.value

        if x[node.feature] <= node.threshold:
            return self._traverse_tree(x, node.left)
        return self._traverse_tree(x, node.right)


class RandomForestModel(object):

    def __init__(self, n_estimators):
        self.estimators = n_estimators
        models = []
        for x in range(n_estimators):
            models.append(DecisionTreeModel(max_depth=10))
        self.models = models

    def fit(self, X: pd.DataFrame, y: pd.Series):
        for model in self.models:
            random_rows = random.choices(range(X.shape[0]), k=X.shape[0])
            X_train = X.iloc[random_rows]
            y_train = y.iloc[random_rows]
            model.fit(X_train, y_train)

    def predict(self, X: pd.DataFrame):
        predict_set = pd.DataFrame()
        c = 0
        for model in self.models:
            predict_set[++c] = model.predict(X)

        prediction = predict_set.mode(axis=1).iloc[:, 0]
        return prediction.to_numpy()


def accuracy_score(y_true, y_pred):
    accuracy = np.sum(y_true == y_pred) / len(y_true)
    return accuracy


def classification_report(y_test, y_pred):
    confusion = confusion_matrix(y_test, y_pred)
    result = {}
    labels = confusion.columns
    for idx, label in enumerate(labels):
        alt_idx = 1 if idx == 0 else 0
        TP = confusion[labels[alt_idx]][labels[alt_idx]]
        FP = confusion[labels[alt_idx]][labels[idx]]
        FN = confusion[labels[idx]][labels[alt_idx]]
        TN = confusion[labels[idx]][labels[idx]]

        precision = TP / (TP + FP)
        recall = TP / (TP + FN)
        f1 = 2 * (precision * recall)/ (precision + recall)
        support = TN + FP
        result[label] = {'precision': precision,
                         'recall': recall,
                         'f1-score': f1,
                         'support': support
                         }

        return result


def confusion_matrix(y_test, y_pred):
    # return the 2x2 matrix
    # format = [[TP, FN],
    #           [FP, TN]]

    # We inialize the result as a 2x2 array with zeros
    # Go through all elements in the test. Find all instances of TP, TN, FP, FN

    return pd.crosstab(y_test, y_pred)

def _test():
    df = pd.read_csv('breast_cancer.csv')

    # X = df.drop(['diagnosis'], axis=1).to_numpy()
    # y = df['diagnosis'].apply(lambda x: 0 if x == 'M' else 1).to_numpy()

    X = df.drop(['diagnosis'], axis=1)
    y = df['diagnosis']
    # y = df['diagnosis'].apply(lambda x: 0 if x == 'M' else 1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=1
    )

    clf = DecisionTreeModel(max_depth=10)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("Accuracy:", acc)

if __name__ == "__main__":
    _test()
