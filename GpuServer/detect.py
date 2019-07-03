#!/usr/bin/env python
# coding: utf-8

import os
import sys
import random
import math
import re
import time
import numpy as np
import tensorflow as tf
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Root directory of the project
# ROOT_DIR = os.path.abspath("../../")
ROOT_DIR = "/home/gpu_user/Mask_RCNN"

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from mrcnn import utils
# from mrcnn import visualize
# from mrcnn.visualize import display_images
from mrcnn import visualizeLeaf as visualize
from mrcnn.visualizeLeaf import display_images
import mrcnn.model as modellib
from mrcnn.model import log

from samples.leaf import leaf

# Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs")
LEAF_WEIGHTS_PATH = os.path.join(MODEL_DIR, "leaf20190528T1358/mask_rcnn_leaf_0027.h5")  # update this path


# Configurations
config = leaf.CustomConfig()

# Override the training configurations with a few
# changes for inferencing.
class InferenceConfig(config.__class__):
    # Run detection on one image at a time
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

config = InferenceConfig()
#config.display()


# ## Notebook Preferences

# Device to load the neural network on.
# Useful if you're training a model on the same 
# machine, in which case use CPU and leave the
# GPU for training.
DEVICE = "/cpu:0"  # /cpu:0 or /gpu:0

# Inspect the model in training or inference modes
# values: 'inference' or 'training'
TEST_MODE = "inference"

def get_ax(rows=1, cols=1, size=16):
    """Return a Matplotlib Axes array to be used in
    all visualizations in the notebook. Provide a
    central point to control graph sizes.
    
    Adjust the size attribute to control how big to render images
    """
    _, ax = plt.subplots(rows, cols, figsize=(size*cols, size*rows))
    return ax


# ## Load Model

# Create model in inference mode
with tf.device(DEVICE):
    model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR,
                              config=config)

# Set path to leaf weights file
weights_path = LEAF_WEIGHTS_PATH

# Or, load the last model you trained
#weights_path = model.find_last()

# Load weights
print("Loading weights ", weights_path)
model.load_weights(weights_path, by_name=True)


# ## Run Detection
def analysePlant(image_path, image_name):
    import cv2
    bgrimage = cv2.imread(image_path)
    image = cv2.cvtColor(bgrimage, cv2.COLOR_BGR2RGB)
    # Run object detection
    results = model.detect([image], verbose=0) #pass image array to detect

    # Display results
    ax = get_ax(1)
    r = results[0] #only 1 image in image array

    class_names = ['BG','leaf']
    data = visualize.save_instances(image, image_name, r['rois'], r['masks'], r['class_ids'], 
                                class_names, r['scores'], ax=ax,
                                title="Predictions")
    return data

    # ## Color Splash
    # 
    # This is for illustration. You can call `leaf.py` with the `splash` option to get better images without the black padding.

    #splash = leaf.color_splash(image, r['masks'])
    #display_images([splash], cols=1)

if __name__ == '__main__':
    image_name="36.png"
    image_path= os.path.join("/home/gpu_user/Mask_RCNN/datasets/leaf/val/"+image_name)
    analysedData = analysePlant(image_path, image_name)
    print(analysedData)
    