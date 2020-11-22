
'''
imports and global
'''
from os.path import dirname, abspath
import sys
d = dirname(dirname(dirname((__file__))))
sys.path.append(d)
import utils.helper as helper
import numpy as np

import tensorflow as tf
from tensorflow import keras
from keras_tqdm import TQDMCallback
from keras.callbacks import ModelCheckpoint

import os
os.environ['SM_FRAMEWORK'] = 'tf.keras'
SM_FRAMEWORK = os.getenv('SM_FRAMEWORK')
import segmentation_models_dev as sm
sm.set_framework(SM_FRAMEWORK)

# import wandb
# from wandb.keras import WandbCallback

from utils.datagen import get_dataset

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)

        
''' 
---------------------------------------
GLOBAL - CHANGE HERE
--------------------------------------- 
''' 

BACKBONE = 'resnet18' # from architecture_trial_resnet
# wandb.init(project='external_parameter_decoderblocktype')
# config = wandb.config
# config.project_description = 'upsampling'
model_name = 'external_parameter_decoderblocktype_upsampling'
augment = False

learning_rate = 10e-4 # from external_parameter_learningrate
loss = sm.losses.JaccardLoss()  # from external_parameter_loss
optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)  # from external_parameter_optimizer
decoder_block_type = 'upsampling'


'''
loading data in the form of tf.data.dataset
'''
PATH_RESULTS, PATH_HISTORIES, PATH_FIGURES, PATH_CHECKPOINTS, PATH_PREDICTIONS, PATH_SAMPLE_FIGS = helper.results_paths()

print('reading tf.data.Dataset')
train_data = get_dataset('./data_project/train/SN_6.tfrecords', augment=augment)
val_data = get_dataset('./data_project/train/SN_6_val.tfrecords')
test_data = get_dataset('./data_project/test/SN_6_test.tfrecords')
print("tf.data.Dataset for train/val/test read")


'''
define the model - make sure to set model name
'''
model = sm.Unet(BACKBONE, encoder_weights='imagenet', input_shape=(None, None, 3), decoder_block_type=decoder_block_type)
model.compile(
    optimizer=optimizer,
    loss=loss,
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
   steps_per_epoch=105,
   validation_steps=45,
   callbacks=[
       TQDMCallback(),
       # WandbCallback(log_weights=True, save_weights_only=True),
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

test_metrics = model.evaluate(test_data, steps=3)

test_metrics_dict = {
    'test_loss': test_metrics[0],
    'test_iou_score': test_metrics[1]
}

np.save(PATH_PREDICTIONS/str(model_name + "_prediction_score"), test_metrics_dict)