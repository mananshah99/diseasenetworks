'''
randomforest.py

Description: Provides methods to train and apply the random forest classifier
(although normally used as a regressor, individual decision tree weights may
also be applied in a classifying fashion).

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''
import numpy as np
import csv
import cPickle

from sklearn.ensemble import RandomForestClassifier as RandomForest
from sklearn.cross_validation import StratifiedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from quadratic_weighted_kappa import *

np.set_printoptions(threshold='nan')

def get_train_data(features_path):
    ls = list(csv.reader(open(features_path, "rb"), delimiter=','))
    nls = []
    out = []
    for row in ls:
        out.append(row[-1])
        row = row[:-1]
        nls.append(row)
    X = np.array(nls, dtype=float)
    y = np.array(out)
    y = y.astype('int')
    return X, y

def cross_validation():
    X, y = get_train_data('features.csv');

    # Parameters space creation
    params_space = [[200]]

    # Grid search
    grid_errors = []
    for params in params_space:
        # Cross validation
        skf = StratifiedKFold(y, n_folds=8)
        errors = []
        for train, test in skf:
            clf = RandomForest(n_estimators=params[0], n_jobs=2)
            clf.fit(X[train], y[train])
            predictions = clf.predict(X[test])
            kappa_score = quadratic_weighted_kappa(y[test], predictions)
            print "Kappa: %f" % kappa_score
            print "Confusion matrix:"
            print confusion_matrix(y[test], predictions)
            print "Classification report:"
            print classification_report(y[test], predictions)
            errors.append(kappa_score)
        grid_errors.append(np.mean(errors))
    # Show results
    print "Kappa: " + str(grid_errors)

def save_model(model):
    with open('rf.cpickle', 'wb') as f:
        cPickle.dump(model, f)

def model(feature_file, estimators):
    X, y = get_train_data(feature_file) #After last comma should be the class
    clf = RandomForest(n_estimators=estimators, n_jobs=1)
    clf.fit(X, y)
    save_model(clf)

def make_predictions(feature_file, model_file):
    with open(model_file, 'rb') as f:
        rf = cPickle.load(f)

    ls = list(csv.reader(open(feature_file, "rb"), delimiter=','))
    X = np.array(ls, dtype=float)
    predictions = rf.predict(X)
    return predictions
