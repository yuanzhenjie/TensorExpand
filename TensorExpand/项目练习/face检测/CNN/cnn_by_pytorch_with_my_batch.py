#! /usr/bin/python
# -*- coding: utf8 -*-

'''
自定义批训练，不使用torch自带的批训练

输入 x 数据类型必须是：float32、float64  shape[none,c,h,w] ,tensorflow [none,h,w,c]
输入 y 数据类型必须是：int64  (uint8、int16、int32 均报错)，且是非 one_hot标签

# pytorch only supported types are: double, float, int64, int32, and uint8.
x=np.array([1,2,3],np.float16) # float16
x=torch.from_numpy(x) # 报错
x=Variable(x) # 报错

x=np.array([1,2,3],np.float32) # float32 (float)
x=torch.from_numpy(x) # FloatTensor
x=Variable(x) # FloatTensor

# np.float 等价于np.float64
x=np.array([1,2,3],np.float64) # float64 (double)
x=torch.from_numpy(x) # DoubleTensor
x=Variable(x) # DoubleTensor

x=np.array([1,2,3],np.uint8) # uint8
x=torch.from_numpy(x) # ByteTensor
x=Variable(x) # ByteTensor

x=np.array([1,2,3],np.int8) # int8
x=torch.from_numpy(x) # # 报错
x=Variable(x) # # 报错

x=np.array([1,2,3],np.int16) # int16
x=torch.from_numpy(x) # ShortTensor
x=Variable(x) # ShortTensor

# np.int 等价于np.int32
x=np.array([1,2,3],np.int32) # int32
x=torch.from_numpy(x) # IntTensor
x=Variable(x) # IntTensor

x=np.array([1,2,3],np.int64) # int64
x=torch.from_numpy(x) # LongTensor
x=Variable(x) # LongTensor
'''

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.utils.data as Data
import pandas as pd
# import tensorflow as tf
import numpy as np
import glob

# Parameters
learning_rate = 0.001
training_iters = 2000
batch_size = 64
display_step = 10
EPOCH=3

# Network Parameters
img_h=19
img_w=19
img_c=4
n_input = img_h*img_w*img_c
n_classes = 2 #
dropout = 0.75 #


# 加载数据
filepaths=glob.glob('./data_*.pkl')
for i,filepath in enumerate(filepaths):
    if i==0:
        data=pd.read_pickle(filepath)
    else:
        data=np.vstack((data,pd.read_pickle(filepath)))
# np.random.shuffle(data)
'''
# Data Loader for easy mini-batch return in training, the image batch shape will be (50, 1, 28, 28)
# train_loader = Data.DataLoader(dataset=data, batch_size=batch_size, shuffle=True)
xx=np.reshape(data[:,:-1],[-1,img_h,img_w,img_c]).transpose([0,3,1,2]).astype(np.float32) # [-1,4,19,19]
yy=data[:,-1].astype(np.uint8)
torch_dataset = Data.TensorDataset(data_tensor=torch.from_numpy(xx), target_tensor=torch.from_numpy(yy))

# 把 dataset 放入 DataLoader
loader = Data.DataLoader(
    dataset=torch_dataset,      # torch TensorDataset format
    batch_size=batch_size,      # mini batch size
    shuffle=True,               # 要不要打乱数据 (打乱比较好)
    num_workers=2,              # 多线程来读数据
)
'''
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Sequential(         # input shape (4, 19, 19)
            nn.Conv2d(
                in_channels=img_c,              # input height
                out_channels=32,            # n_filters
                kernel_size=5,              # filter size
                stride=1,                   # filter movement/step
                padding=2,                  # if want same width and length of this image after con2d, padding=(kernel_size-1)/2 if stride=1
            ),                              # output shape (32, 19, 19)
            nn.ReLU(),                      # activation
            nn.MaxPool2d(kernel_size=2),    # choose max value in 2x2 area, output shape (32, 9, 9)
        )
        self.conv2 = nn.Sequential(         # input shape (32, 9, 9)
            nn.Conv2d(32, 64, 5, 1, 2),     # output shape (64, 9, 9)
            nn.ReLU(),                      # activation
            nn.MaxPool2d(2),                # output shape (64, 4, 4)
        )
        self.out = nn.Linear(64 * 4 * 4, n_classes)   # fully connected layer, output 10 classes

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = x.view(x.size(0), -1)           # flatten the output of conv2 to (batch_size, 64 * 5 * 5)
        output = self.out(x)
        return output#, x    # return x for visualization

# cnn = CNN().double()
cnn=CNN()
print(cnn)  # net architecture

optimizer = torch.optim.Adam(cnn.parameters(), lr=learning_rate)   # optimize all cnn parameters
loss_func = nn.CrossEntropyLoss()                       # the target label is not one-hotted

# training and testing
for epoch in range(EPOCH):
    np.random.shuffle(data)
    start = 0
    end = 0
    for step in range(1000):
        end = min(len(data), start + batch_size)
        train_data = data[start:end]

        if end == len(data):
            start = 0
        else:
            start = end

        x = np.reshape(train_data[:, :-1], [-1, img_h, img_w, img_c]).transpose([0, 3, 1, 2]).astype(
            np.float32)  # [-1,4,19,19] 必须先转成float32、float64
        y = train_data[:, -1].astype(np.int64) # 必须转成int64 (uint8、int16、int32 均报错)，且是非 one_hot标签

        x=torch.from_numpy(x) # numpy-->torchTensor
        y=torch.from_numpy(y)

        b_x = Variable(x)   # torchTensor--> Variable
        b_y = Variable(y)   # batch y

        output = cnn(b_x)             # cnn output
        loss = loss_func(output, b_y)   # cross entropy loss
        optimizer.zero_grad()           # clear gradients for this training step
        loss.backward()                 # backpropagation, compute gradients
        optimizer.step()                # apply gradients

        if step % 50 == 0:
            # test_output = cnn(test_x)
            pred_y = torch.max(output, 1)[1].data.squeeze() # LongTensor 非Variable
            accuracy = sum(pred_y == y) / float(y.size(0))
            print('Epoch: ', epoch, '| train loss: %.4f' % loss.data[0], '| test accuracy: %.2f' % accuracy)
