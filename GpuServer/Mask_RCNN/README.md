# greenServer
The Green server uses matterport/Mask_RCNN project adapted for leaf segmentation.

# Leaf Segmentation

This is an example showing the use of Mask RCNN in a real application.
We train the model to detect leaves only and segment it out from rest of the image.

This is a sample Image given to the model
![Original Image](https://raw.githubusercontent.com/ajaichemmanam/greenServer/master/GpuServer/Mask_RCNN/assets/c3i-strawberry2.jpg)

Segmented Image Obtained
![Segmented Image](https://raw.githubusercontent.com/ajaichemmanam/greenServer/master/GpuServer/Mask_RCNN/assets/mask_c3i-strawberry2.jpg)
## Installation

1. Download and Install Shapely using whl file downloaded from
https://www.lfd.uci.edu/~gohlke/pythonlibs/

2. Do pip install requirements.txt

3. Download Sample Model: https://drive.google.com/open?id=1NBw6xIVuntBsjWfYji6Fdd9gPKkpKtxX Save it in the root directory of the repo (the `mask_rcnn` directory).
4. Copy Dataset to `mask_rcnn/datasets/leaf/`.

## Run Jupyter notebooks
Open the `inspect_leaf_data.ipynb` or `inspect_leaf_model.ipynb` Jupter notebooks. You can use these notebooks to explore the dataset and run through the detection pipelie step by step.

## Creating Dataset
1. Create a train and val folders containing images of leaves.
2. Open http://www.robots.ox.ac.uk/~vgg/software/via/via-1.0.6.html
3. Load Images and start annotating the leaves in the images using POLYGON tool.
4. Click on Region Attributes and add column as name and as  attribute leaf
![Image Annotation](https://raw.githubusercontent.com/ajaichemmanam/greenServer/master/GpuServer/Mask_RCNN/assets/image_anotation.PNG)

5. After annotating all the images, Click Save as JSON in Annotation dropdown.
6. Save annotation as via_region_data.json and copy to the folder contaning the images


## Training the model

Train a new model starting from pre-trained COCO weights
```
python3 leaf.py train --dataset=/path/to/leaf/dataset --weights=coco
```

Resume training a model that you had trained earlier
```
python3 leaf.py train --dataset=/path/to/leaf/dataset --weights=last
```

Train a new model starting from ImageNet weights
```
python3 leaf.py train --dataset=/path/to/leaf/dataset --weights=imagenet
```

The code in `leaf.py` is set to train for 3K steps (30 epochs of 100 steps each), and using a batch size of 2. 
Update the schedule to fit your needs.

## Credits
Matterport