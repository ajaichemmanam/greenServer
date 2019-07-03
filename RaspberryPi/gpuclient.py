import os
import base64
import requests
import json

#img_name = "52.png"
#img_dir = "/home/gpu_user/Mask_RCNN/datasets/leaf/val/"
#with open(os.path.join(img_dir+img_name), 'rb') as img_file:
    # read the image file
    #data = img_file.read()
    #encoded_string = base64.b64encode(data) 

# build JSON object
#outjson = {}
#outjson['filename']= img_name
#outjson['image'] = data.encode('base64')   # data has to be encoded base64
#outjson['image'] = encoded_string
#json_data = json.dumps(str(outjson))

import numpy as np
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
#img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

retval, img_data = cv2.imencode('.jpg', frame)
img_data = img_data.tobytes()
encoded_string = base64.b64encode(img_data).decode('utf-8') 

img_name = input("Enter Plant ID: ")
img_name += ".jpg"
json_data={"filename":img_name, "image":encoded_string}

print(json_data)
url = "http://172.26.234.2:5000/postjson"
response = requests.post(url, json=json_data)
print(response.json())

cap.release()