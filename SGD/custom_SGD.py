import math
import os
import sys
sys.path.append("../")
import time
import timeit

import matplotlib.pyplot as plt
import numpy as np  # linear algebra
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
from numpy.core.umath_tests import inner1d
from pandas.api.types import CategoricalDtype
from sklearn import ensemble, linear_model, metrics, model_selection
from sklearn.datasets import load_breast_cancer, make_regression, make_classification
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sklearn.preprocessing import LabelBinarizer
from utils import custom_scores, dataset_helper


__RANDOM_STATE = 42
__iteration_log = []

# -----------------------------------
#   Softmax Classify Methods
# -----------------------------------


def classify_softmax(theta, X):
    X = np.insert(X, 0, 1, axis=1)
    h = softmax(theta, X)
    pred = np.argmax(h, axis=0)
    X = np.delete(X, 0, axis=1)
    return pred
    
def get_iteration_log():
    global __iteration_log
    cols = len(__iteration_log[0])
    print(cols)
    df = pd.DataFrame(__iteration_log, columns=[
                      'it', 'b_it', 'epoch', 'acc_train', 'eta', 'acc_val'][:cols])
    df.set_index(df.it)
    return df


def get_batch(X, y, b_it, b_sz, epoch):
    b_ct = int(X.shape[0]/b_sz)
    y_ = np.zeros((0, 0))
    X_ = np.zeros((0, 0))
    start = 0
    finish = 0

    if b_it > b_ct:
        b_it = 0
        epoch += 1
    start = b_it * b_sz
    finish = (b_it+1) * b_sz
    X_ = X[start: finish]
    y_ = y[start: finish]

    b_it += 1

    return X_, y_, b_it, epoch


def get_batch_test():
    count = 105
    X = np.ones((count, 3))
    y = np.array(range(0, count))
    b_it = 0
    b_sz = 100
    epoch = 0
    it = 0
    sz = 0
    while epoch < 1:
        X_, y_, b_it, epoch = get_batch(X, y, b_it, b_sz, epoch)
        sz += X_.shape[0]
        print(it, sz, X_.shape, y_.shape, b_it, b_sz, epoch)
        print(y_)
        it += 1


'''
 Since we are dealing with logistic regression,
 the hypothesis is defined as:

                    1
       F(x) = ----------------
                1 + exp^(-x)

 However, its implementation may result in overflow
 if x is too large, then, the version implemented 
 here is more stable with similar results, and is
 defined as:
 
                  exp^(x)
       F(x) = ----------------, if x < 0
                1 + exp^(x) 
                
                    1
       F(x) = ----------------, if x >= 0
                1 + exp^(-x) 
'''


def hypothesis(theta, X, stable=False):
    """
        Given Theta value and the X set it returns the logistic value for its instances.
    """
    dot = np.dot(X, theta)

    # Regular Sigmoid Function
    if (stable == False):
        h = 1 / (1 + np.exp(-dot))

    else:
        # Stable Sigmoid Function
        num = (dot >= 0).astype(np.float128)
        dot[dot >= 0] = -dot[dot >= 0]
        exp = np.exp(dot)
        num = np.multiply(num, exp)
        h = num / (1 + exp)

    return h


def softmax(theta, X):
    score = np.dot(theta, X.transpose())
    exp = np.exp(score)
    h = exp / np.sum(exp, axis=0)
    return h


def classify(theta, X, th=0.5, binary=True, multinomial_=False):
    """
        Given a threshold apply a binary classification of the samples regarding an optimized theta
    """
    if ((binary) and (not multinomial_)):        
        if theta.shape[0] > X.shape[1]:
            X = np.insert(X, 0, 1, axis=1)
        y = hypothesis(theta, X)
        y = np.where(y >= th, 1, 0)
        X = np.delete(X, 0, axis=1)
    else:
        y = classify_multiclass(theta, X)
    return y


def classify_multiclass(theta, X):
    """
        Apply a multi class classification of the samples regarding an optimized set of thetas
    """
    X = np.insert(X, 0, 1, axis=1)

    # Running the M models for each instance
    probs = np.array([hypothesis(theta[m], X) for m in theta.keys()])
    # Inverting the Matrix from (Models, X) to (X, Models)
    probs = probs.T
    # Getting the max probability for each x in X
    labels = probs.argmax(axis=1)

    X = np.delete(X, 0, axis=1)
    return labels


def classify_softmax(theta, X):
    X = np.insert(X, 0, 1, axis=1)
    h = softmax(theta, X)
    labels = np.argmax(h, axis=1)
    X = np.delete(X, 0, axis=1)
    return labels


def cross_entropy_loss(h, y):
    """
     y.log(h) + (1-log(h) . 1-y)
     log probability * inverse of the log probabality
    """
    eps = np.finfo(np.float).eps
    h[h < eps] = eps
    h[h > 1.-eps] = 1.-eps
    return np.multiply(np.log(h), y) + np.multiply((np.log(1-h)), (1-y))


def grad_logit_step(theta, X, y, alpha, error):
    """
        Given the current Theta Set it calculates the gradient and new values for it.
    """
    grad = np.dot(X.transpose(), error)/len(y)
    result = theta - alpha * grad

    return result


def grad_logit_step_test():
    theta = np.array([1, 0, 0], dtype='float64')
    theta_temp = np.array([0, 0, 0], dtype='float64')
    X, y = get_toy_data()
    X = np.insert(X, 0, 1, axis=1)

    alpha = .9
    max_iter = 50
    for i in range(max_iter):
        h0 = hypothesis(theta, X)
        error = (h0 - y)

        theta_temp = grad_logit_step(theta, X, y, alpha, error)

        theta = theta_temp.copy()
        print("Iter %i theta: %s" % (i, theta))
        y_hat = classify(theta, X)
        print("Training Accuracy: %.3f" %
              custom_scores.accuracy_score(y, y_hat))

    theta = np.array(theta)
    print("Predicted: %s" % (hypothesis(theta, X)))
    print("Expected: %s" % (y))


def get_toy_data():
    y = np.array([1., 0.], dtype='float64')
    X = np.array([[4., 7.], [2., 6.]], dtype='float64')
    return X, y


def get_toy_data_binary():
    """
        Returns  X_train, X_test, y_train, y_test from Breast Cancer
    """
    X, y = load_breast_cancer(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=__RANDOM_STATE)
    return X_train, X_test, y_train, y_test


def get_toy_data_multiclass():
    """
        Returns  X_train, X_test, y_train, y_test from with 4 classes and 20 features
    """
    X, y = make_classification(n_samples=500, n_features=10, n_classes=4,
                               n_clusters_per_class=1, n_informative=4,
                               n_redundant=0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=__RANDOM_STATE)

    return X_train, X_test, y_train, y_test


def SGD(lr, max_iter, X, y, lr_optimizer=None,
        power_t=0.25, t=1.0,
        batch_type='Full',
        batch_sz=1,
        print_interval=100,
        X_val=None,
        y_val=None,
        multinomial=False):

    # Adding theta0 to the feature vector
    X = np.insert(X, values=1, obj=0, axis=1)
    y = y.transpose()
    shape = X.shape
    nsamples = shape[0]
    print("Number of samples: "+str(nsamples))
    nparams = shape[1]
    print("Number of parameters: "+str(nparams))

    if multinomial:        
        theta = np.zeros([y.shape[0], nparams])
        theta_temp = np.ones([y.shape[0], nparams])
        print(theta.shape)
        return 0
    else:
        theta = np.zeros(nparams)
        theta_temp = np.ones(nparams)

    error = 1
    it = 0
    epoch = 0
    lst_epoch = 0
    b_it = 0

    if batch_type == 'Full':
        b_sz = nsamples
    else:  # Mini or Stochastic
        b_sz = batch_sz

    if batch_type == 'Stochastic':
        X, y = shuffle(X, y)
        print('Shuffled')
    global __iteration_log
    __iteration_log = []
    acc_val = 0.    
    while (it < max_iter):
        if lr_optimizer == 'invscaling':
            eta = lr / (it + 1) * pow(t, power_t)
        else:
            eta = lr

        X_ = np.zeros(0)
        y_ = np.zeros(0)        
        if batch_type == 'Full':
            X_, y_ = (X, y)
            epoch +=  1
        else:
            while y_.shape[0] == 0:
                # Checking if it is a new epoch to shuffle the data.
                X_, y_, b_it, epoch = get_batch(X, y, b_it, b_sz, epoch)
                if lst_epoch < epoch:
                    lst_epoch = epoch
                    if batch_type == 'Stochastic':
                        X, y = shuffle(X, y)
        
        if multinomial:            
            h = softmax(theta, X)

            error = h - y_
            grad = (np.matmul(error, X_))/nsamples
            theta_temp = theta - (eta*grad)            
            y_pred = classify_softmax(theta_temp, X_)
            
        else:
            h0 = hypothesis(theta, X_)

            error = (h0 - y_)                        
            theta_temp = grad_logit_step(theta, X_, y_, eta, error)
            y_pred = classify(theta_temp, X_)
        
        
        acc_train = custom_scores.accuracy_score(y_, y_pred)

        theta = theta_temp.copy()

        it += 1
        t += 1

        if X_val is not None:            
            if multinomial: 
                y_pred_val = classify_softmax(theta, X_val)
            else: 
                y_pred_val = classify(theta, X_val)
            acc_val = custom_scores.accuracy_score(y_val, y_pred_val)

        if (it % print_interval) == 0 or it == 1:
            if X_val is not None:
                print("It: %s Batch: %s Epoch %i Error %0.8f Train Acc: %.8f lr: %.8f Val Acc: %.8f" %
                      (it, b_it, epoch, error.mean(), acc_train, eta, acc_val))
            else:
                print("It: %s Batch: %s Epoch %i Train Acc : %.8f lr: %.8f " %
                      (it, b_it, epoch, acc_train, eta))

        if X_val is not None:
            __iteration_log.append((it, b_it, epoch, acc_train, eta, acc_val))
        else:
            __iteration_log.append((it, b_it, epoch, acc_train, eta))

    if multinomial: 
        y_pred = classify_softmax(theta, X)
    else: 
        y_pred = classify(theta, X)
    
    
    acc_train = custom_scores.accuracy_score(y, y_pred)

    if X_val is not None:
        print("Finished \n Whole Set Train Acc: %.8f Val Acc: %.8f" %
              (acc_train, acc_val))
        __iteration_log.append((it, b_it, epoch, acc_train, eta, acc_val))
    else:
        print("Finished \n Whole Set Train Acc: %.8f " %
              (acc_train))
        __iteration_log.append((it, b_it, epoch, acc_train))
    return theta


def SGD_one_vs_all(lr, max_iter, X, y, lr_optimizer=None,
                   power_t=0.25, t=1.0,
                   batch_type='Full',
                   batch_sz=1,
                   print_interval=100,
                   X_val=None,
                   y_val=None):

    classes = np.unique(y)
    print(classes)
    theta = {}

    for c in classes:
        print("==============================================")
        print("Training for class {}".format(c))
        print("==============================================")
        cy = np.copy(y)
        cy[y != c] = 0.
        cy[y == c] = 1.

        cy_val = np.copy(y_val)
        cy_val[y_val != c] = 0.
        cy_val[y_val == c] = 1.

        theta[c] = SGD(lr, max_iter, X, cy, lr_optimizer,
                       power_t, t,
                       batch_type,
                       batch_sz,
                       print_interval,
                       X_val,
                       cy_val)
        print("==============================================")

    return theta


def SGD_softmax(lr, max_iter, X, y, lr_optimizer=None,
                power_t=0.25, t=1.0,
                batch_type='Full',
                batch_sz=1,
                print_interval=100,
                X_val=None,
                y_val=None, nclasses=10):

            
    print("==============================================")
    print("Training softmax model")
    print("==============================================")

    theta = SGD(lr, max_iter, X, y, batch_type='Full',
                    batch_sz=batch_sz, print_interval=print_interval, 
                    X_val=X_val, y_val = y_val, multinomial=True)
    print("==============================================")

    return theta


def SGD_test_binary():
    X,  X_val, y, y_val = get_toy_data_binary()

    lr = .01
    max_iter = 1000
    batch_sz = 64
    print_interval = 100

    print("")
    print("Full batch")

    start = time.process_time()
    theta = SGD(lr, max_iter, X, y, batch_type='Full',
                lr_optimizer='invscaling', print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val)
    evalute_binary(y_val, y_pred)

    print("")
    print("Stochastic Mini batch")
    start = time.process_time()
    theta = SGD(lr, max_iter, X, y, batch_type='Stochastic',
                batch_sz=batch_sz,  lr_optimizer='invscaling', print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val)
    evalute_binary(y_val, y_pred)

    print("")
    print("Mini batch")
    start = time.process_time()
    theta = SGD(lr, max_iter, X, y, batch_type='Mini',
                batch_sz=batch_sz,  lr_optimizer='invscaling', print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val)
    evalute_binary(y_val, y_pred)

    print("")
    print("Single Instance")
    start = time.process_time()
    theta = SGD(lr, max_iter, X, y, batch_type='Single',
                batch_sz=1,  lr_optimizer='invscaling', print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val)
    print(y_pred.shape, y_val.shape)
    evalute_binary(y_val, y_pred)


def evalute_binary(y_val, y_pred):
    print("Validation Stats...\nAccuracy: %.3f" %
          custom_scores.accuracy_score(y_val, y_pred))
    print("Precision: %.3f" % custom_scores.precision_score(y_val, y_pred))
    print('Recall: %.3f' % custom_scores.recall_score(y_val, y_pred))
    print('F1 Score: %3f' % custom_scores.f1_score(y_val, y_pred))
    custom_scores.compute_confusion_matrix(y_val, y_pred)


def SGD_toy_test_multiclass():
    X,  X_val, y, y_val = get_toy_data_multiclass()

    lr = .001
    max_iter = 100
    batch_sz = 64
    print_interval = 1000

    print("")
    print("Stochastic Mini batch")
    start = time.process_time()
    theta = SGD_one_vs_all(lr, max_iter, X, y, batch_type='Stochastic',
                           batch_sz=batch_sz, print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val, binary=False)
    evalute_multiclass(y_val, y_pred)


def SGD_test_multiclass(scaling_type):
    X, y, _, _ = dataset_helper.load_fasion_mnist()

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=1)

    lr = .0001
    max_iter = 50000
    print_interval = 1000

    print("")
    print("Stochastic Mini batch")
    print("----------------------------")
    print("Number of Iterations:", max_iter)
    print("Learning rate:", lr)
    print("----------------------------")
    start = time.process_time()
    theta = SGD_one_vs_all(lr, max_iter, X_train, y_train, 
                           batch_sz=1, print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify(theta, X_val, binary=False)
    evalute_multiclass(y_val, y_pred)


def SGD_test_multiclass_softmax(scaling='default'):
    X, y, _, _ = dataset_helper.load_fasion_mnist()

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=1)

    lr = .01
    max_iter = 50
    batch_sz = 64
    print_interval = 1

    print("")
    print("Stochastic Mini batch")
    print("----------------------------")
    print("Number of Iterations:", max_iter)
    print("Learning rate:", lr)
    print("----------------------------")
    start = time.process_time()
    theta = SGD_softmax(lr, max_iter, X_train, y_train, batch_type='Full',
                        batch_sz=batch_sz, print_interval=print_interval)
    print("Time Spent ", time.process_time() - start)
    y_pred = classify_softmax(theta, X_val)
    evalute_multiclass(y_val, y_pred)


def evalute_multiclass(y_val, y_pred):
    print("Validation Stats...\nAccuracy: %.3f" %
          custom_scores.accuracy_score(y_val, y_pred, mode='multi'))
    print("Precision: %.3f" %
          custom_scores.precision_score(y_val, y_pred, mode='multi'))
    print('Recall: %.3f' % custom_scores.recall_score(
        y_val, y_pred, mode='multi'))
    print('F1 Score: %3f' % custom_scores.f1_score(y_val, y_pred, mode='multi'))

    custom_scores.compute_confusion_matrix(y_val, y_pred)
