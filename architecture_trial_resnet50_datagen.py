
'''
imports and global
'''
import utils.helper as helper
import numpy as np

import tensorflow as tf
from tensorflow import keras
from keras_tqdm import TQDMCallback
from keras.callbacks import ModelCheckpoint

import os
os.environ['SM_FRAMEWORK'] = 'tf.keras'
SM_FRAMEWORK = os.getenv('SM_FRAMEWORK')
import segmentation_models as sm
sm.set_framework(SM_FRAMEWORK)

import wandb
from wandb.keras import WandbCallback

from utils.datagen import get_dataset

''' 
---------------------------------------
GLOBAL - CHANGE HERE
--------------------------------------- 
''' 

BACKBONE = 'resnet50'
wandb.init(project='architecture_trial_resnet50_datagen')
model_name = 'architecture_trial_resnet50_datagen'





'''
load your data. this is a 5GB numpy array with all our data
'''
print("loading data")
PATH_RESULTS, PATH_HISTORIES, PATH_FIGURES, PATH_CHECKPOINTS, PATH_PREDICTIONS = helper.results_paths()
X_train, Y_train, X_test, Y_test = helper.generate_train_test()
print("X_train, Y_train, X_test, Y_test loaded")


'''
preprocess input to ensure it fits the model definition
'''
print("preprocessing input")
preprocess_input = sm.get_preprocessing(BACKBONE)

print('reading tf.data.Dataset')
train_data = get_data('./data_project/train/SN_6.tfrecords', train=True)
val_data = get_data('./data_project/train/SN_6_val.tfrecords', train=False)
test_data = get_data('./data_project/test/SN_6_test.tfrecords', train=False)

'''
define the model - make sure to set model name
'''
model = sm.Unet(BACKBONE, encoder_weights='imagenet', input_shape=(None, None, 3))
model.compile(
    optimizer='adam',
    loss=sm.losses.BinaryFocalLoss(alpha=0.75, gamma=0.25),
    metrics=[sm.metrics.IOUScore()],
)


'''
fit model - save best weights at each epoch
'''
CheckpointCallback = ModelCheckpoint(str(PATH_CHECKPOINTS / (model_name + '.hdf5')), monitor='val_loss', verbose=1, save_weights_only=True, save_best_only=True, mode='auto', period=1)

history = model.fit(
   train_data,
   epochs=100,
   validation_data=val_data,
   callbacks=[
       TQDMCallback(),
       WandbCallback(log_weights=True),
       CheckpointCallback
       ]
)

helper.history_saver(history, model_name, PATH_HISTORIES, already_npy=False)
history = helper.history_loader(model_name, PATH_HISTORIES)
helper.plot_metrics(history, model_name, PATH_FIGURES)


'''
predict on the test set. load best weights from checkpoints
'''
model.load_weights(str(PATH_CHECKPOINTS / (model_name + '.hdf5')))

# predictions = model.predict(
#     X_test,
#     verbose=1,
#     callbacks=[
#         TQDMCallback()
#     ]
# ) 

test_metrics = model.evaluate(X_test, Y_test, batch_size=16)

test_metrics_dict = {
    'test_loss': test_metrics[0],
    'test_iou_score': test_metrics[1]
}

# np.save(PATH_PREDICTIONS / model_name, predictions)
np.save(PATH_PREDICTIONS/str(model_name + "_prediction_score"), test_metrics_dict)