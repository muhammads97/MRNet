import keras
import numpy as np
import os
from PIL import Image
import random

MAX_PIXEL_VAL = 255
MEAN = 58.09
STDDEV = 49.73

class MRNet_data_generator(keras.utils.Sequence):
  def __init__(self, datapath, IDs, labels, batch_size = 1, shuffle=True,
               scale_to = (256, 256), label_type="abnormal", exam_type="axial",
               train=True, model="vgg", aug_size=8):
    self.path = datapath
    self.n = 0
    self.IDs = IDs
    self.labels = labels
    self.batch_size = batch_size
    self.shuffle = shuffle
    self.scale_to = scale_to
    self.label_type = label_type
    self.exam_type = exam_type
    self.model = model
    self.aug_size=aug_size
    # self.cache_size = cache_size
    if train:
      self.data_path = os.path.join(self.path, "train")
      self.data_type = "train"
    else:
      self.data_path = os.path.join(self.path, "valid")
      self.data_type = "valid"
    # IDs_len = len(self.IDs[self.data_type][self.exam_type])
    # self.n_bachs = int(np.ceil(IDs_len / self.cache_size))
    # self.current = 0
    self.end = self.__len__()
    
    self.on_epoch_end()
    # print("initialized dg")

  def on_epoch_end(self):
    'Updates indexes after each epoch'
    self.indexes = np.arange(len(self.IDs[self.data_type][self.exam_type]))
    # self.current = 0
    # self._next_batch()
    if self.shuffle == True:
        np.random.shuffle(self.indexes)

  def __data_generation(self, list_IDs_temp):
    'Generates data containing batch_size samples' 
    # print("tototototototot")
    # print(list_IDs_temp)
    if self.model == "inception":
      y = np.empty((self.batch_size, 2), dtype=int)
    else:
      y = np.empty((self.batch_size), dtype=int)
    arr = []
    for i, ID in enumerate(list_IDs_temp):
        exam_path = os.path.join(self.data_path, self.exam_type)
        exam = np.load(os.path.join(exam_path, ID+'.npy'))
        e = []
        for s in exam:
          im = Image.fromarray(s)
          s = np.array(im.resize(self.scale_to), dtype=np.float32)
          # standardize
          s = (s - np.min(s)) / (np.max(s) - np.min(s)) * MAX_PIXEL_VAL
          # normalize
          s = (s - MEAN) / STDDEV
          # s = s / np.linalg.norm(s)
          expanded = np.array([s])
          e.append(expanded.reshape((self.scale_to[0], self.scale_to[1], 1)))

        e = np.array(e)
        arr.append(e)
        # X = np.stack(e, axis=0)
        _y = self.labels[ID][self.label_type]
        if self.model == "inception":
          y[i][0] = _y
          y[i][1] = _y
        else:
          y[i] = _y
        
        # y[i] = 155
    X = np.array(arr)
    # print(X.shape, y)
    return X, y
  def __len__(self):
    'Denotes the number of batches per epoch'
    IDs_len = len(self.IDs[self.data_type][self.exam_type])
    return int(np.floor(IDs_len / self.batch_size))

  def __getitem__(self, index):
    'Generate one batch of data'
    # if(index >= self.cache_size*self.current) or (index < self.cache_size*(self.current-1)):
    #   self.current = int(np.floor(index/self.cache_size))
    #   self._next_batch()
    #   return self.__getitem__(index)
    indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
    # print(len(self.indexes))
    list_IDs_temp = [self.IDs[self.data_type][self.exam_type][k] for k in indexes]
    X, y = self.__data_generation(list_IDs_temp)
    X, y = self.augment_data(X[0], y[0], batch_size=self.aug_size)
    return X, y

  def augment_data(self, exam, label, batch_size=1, use_random_rotation=True, use_random_shear=False, use_random_shift=True, use_random_flip=True):
    augmented_batch = []
    augmented_batch_labels = []
    e = []
    for s in range(0, exam.shape[0]):
      scan = exam[s]
      scan = scan.reshape((self.scale_to[0], self.scale_to[1]))
      scan = np.array([scan, scan, scan]).reshape((self.scale_to[0], self.scale_to[1], 3))
      e.append(scan)
    
    augmented_batch.append(e)
    augmented_batch_labels.append(label)
    for i in range (0, batch_size):
      e = []
      for s in range(0, exam.shape[0]):
        scan = exam[s]
        if use_random_rotation:
          scan = keras.preprocessing.image.random_rotation(scan, 25, row_axis=1, col_axis=2, channel_axis=0)
        if use_random_shear:
          scan = keras.preprocessing.image.random_shear(scan, 0.2, row_axis=1, col_axis=2, channel_axis=0)
        if use_random_shift:
          rg = float(25/scan.shape[1])
          scan = keras.preprocessing.image.random_shift(scan, rg, rg, row_axis=1, col_axis=2, channel_axis=0)
        if use_random_flip:
          if bool(random.getrandbits(1)):
            scan = np.fliplr(scan)
        scan = scan.reshape((self.scale_to[0], self.scale_to[1]))
        scan = np.array([scan, scan, scan]).reshape((self.scale_to[0], self.scale_to[1], 3))
        e.append(scan)
      augmented_batch.append(e)
      augmented_batch_labels.append(label)
      # print(len(augmented_batch), augmented_batch[0].shape)
    return np.array(augmented_batch), np.array(augmented_batch_labels)
  # def _load_batch(self, index):
  #   mx = (index+1)*self.cache_size
  #   if(mx >= self.__len__()):
  #     indexes = self.indexes[index*self.cache_size:]
  #   else:
  #     indexes = self.indexes[index*self.cache_size:mx]
  #   list_IDs_temp = [self.IDs[self.data_type][self.exam_type][k] for k in indexes]
  #   X, y = self.__data_generation(list_IDs_temp)
  #   return X, y

  # def _next_batch(self):
  #   if self.current >= self.n_bachs:
  #     self.current = 0
  #   self.batch_x = None
  #   del self.batch_x
  #   self.batch_x, self.batch_y = self._load_batch(self.current)
  #   self.current += 1

  def __next__(self):
    # print("toototot")
    if self.n >= self.end:
      self.n = 0
    result = self.__getitem__(self.n)
    self.n += 1
    return result
