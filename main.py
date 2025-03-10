# Import the libraries
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
from torch.autograd import Variable
from RBM import RBM

# Import the dataset
movies = pd.read_csv('data/ml-1m/movies.dat', sep='::', header=None, engine='python', encoding='latin-1')
users = pd.read_csv('data/ml-1m/users.dat', sep='::', header=None, engine='python', encoding='latin-1')
ratings = pd.read_csv('data/ml-1m/ratings.dat', sep='::', header=None, engine='python', encoding='latin-1')

# Prepare training set and test set
training_set = pd.read_csv('data/ml-100k/u1.base', engine='python', header=None, delimiter='\t')
training_set = np.array(training_set, dtype='int')
test_set = pd.read_csv('data/ml-100k/u1.test', engine='python', header=None, delimiter='\t')
test_set = np.array(test_set, dtype='int')

# Get the number of users and movies
nb_users = int(max(max(training_set[:, 0]), max(test_set[:, 0])))
nb_movies = int(max(max(training_set[:, 1]), max(test_set[:, 1])))


# Create the matrix for the RBM
def convert(data):
    new_data = []
    for id_users in range(1, nb_users + 1):
        id_movies = data[:, 1][data[:, 0] == id_users]
        id_ratings = data[:, 2][data[:, 0] == id_users]
        ratings_list = np.zeros(nb_movies)
        ratings_list[id_movies - 1] = id_ratings
        new_data.append(list(ratings_list))
    return new_data


training_set = convert(training_set)
test_set = convert(test_set)

# Convert data into Torch tensors
training_set = torch.FloatTensor(training_set)
test_set = torch.FloatTensor(test_set)

# Convert the ratings to 1s and 0s
training_set[training_set == 0] = -1
training_set[training_set == 1] = 0
training_set[training_set == 2] = 0
training_set[training_set >= 3] = 1
test_set[test_set == 0] = -1
test_set[test_set == 1] = 0
test_set[test_set == 2] = 0
test_set[test_set >= 3] = 1

# Creating the RBM object
# Number of visible nodes
nv = len(training_set[0])
# Number of hidden nodes
nh = 100
batch_size = 100
rbm = RBM(nv=nv, nh=nh)

# Train the RBM
# Number of epochs to train the RBM
nb_epoch = 10

# Loops through every epoch
for epoch in range(1, nb_epoch + 1):
    # loss error
    train_loss = 0
    # counter
    c = 0.

    # Loops through bathes of users equal to batch_size
    for id_user in range(0, nb_users - batch_size, batch_size):
        # Stores original visible nodes
        vk = training_set[id_user:id_user + batch_size]
        v0 = training_set[id_user:id_user + batch_size]
        ph0, _ = rbm.sample_h(v0)
        # Performs contrastive divergence on the batch
        for k in range(10):
            _, hk = rbm.sample_h(vk)
            _, vk = rbm.sample_v(hk)
            vk[v0 < 0] = v0[v0 < 0]
        phk, _ = rbm.sample_h(vk)
        # Update the rbm weights and bias through training
        rbm.train(v0, vk, ph0, phk)
        # Calculate the loss for analysis
        train_loss += torch.mean(torch.abs(v0[v0 > 0] - vk[v0 > 0]))
        # Add 1 to the counter after every batch completes
        c += 1.
    # loss is normalized using the counter
    normalized_loss = train_loss/c

    # Outputs the user the results of the training
    print('epoch: {ce}/{tc} loss: {l}'.format(ce=epoch, tc=nb_epoch, l=normalized_loss))

# Predict the test set
# Test loss error
test_loss = 0
# Reset counter
c = 0.
for id_user in range(nb_users):
    # Get initial visible nodes
    v = training_set[id_user:id_user+1]
    vt = test_set[id_user:id_user+1]
    # Checks if the user has rated any movies
    if len(vt[vt > 0] > 0):
        # Perform 1 step of gibs sampling on the user
        _, h = rbm.sample_h(v)
        _, v = rbm.sample_v(h)
        # Update the test loss
        test_loss += torch.mean(torch.abs(vt[vt > 0] - v[vt > 0]))
        # Add to the counter
        c += 1.
# Normalize the test loss
normalized_test_loss = test_loss/c
print('test loss: {tl}'.format(tl=normalized_test_loss))

