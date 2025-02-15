#!/usr/bin/python
# ==============================================================================
# Copyright 2018 The Paragon Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


import cv2
import numpy as np
from scipy import ndimage
import sys
import os

import utils as ut


FACE_DIM = (200, 200)
SKIP_FRAME = 2      # the fixed skip frame
frame_skip_rate = 0 # skip SKIP_FRAME frames every other frame
SCALE_FACTOR = 4 # used to resize the captured frame for face detection for faster processing speed
face_cascade = cv2.CascadeClassifier("../classifier/haarcascade_frontalface_default.xml") #create a cascade classifier
sideFace_cascade = cv2.CascadeClassifier('../classifier/haarcascade_profileface.xml')

# dictionary mapping used to keep track of head rotation maps
rotation_maps = {
    "left": np.array([-30, 0, 30]),
    "right": np.array([30, 0, -30]),
    "middle": np.array([0, -30, 30]),
}

def get_rotation_map(rotation):
    """ Takes in an angle rotation, and returns an optimized rotation map """
    if rotation > 0: return rotation_maps.get("right", None)
    if rotation < 0: return rotation_maps.get("left", None)
    if rotation == 0: return rotation_maps.get("middle", None)

current_rotation_map = get_rotation_map(0) 


webcam = cv2.VideoCapture(0)

ret, frame = webcam.read() # get first frame
frame_scale = (frame.shape[1]/SCALE_FACTOR,frame.shape[0]/SCALE_FACTOR)  # (y, x)


cropped_face = []
num_of_face_to_collect = 150
num_of_face_saved = 0


#  For saving face data to directory
profile_folder_path = None

if len(sys.argv) == 1:
    print "\nError: No Saving Diectory Specified\n"
    exit()
elif len(sys.argv) > 2:
    print "\nError: More Than One Saving Directory Specified\n"
    exit()
else: 
    profile_folder_path = ut.create_profile_in_database(sys.argv[1])


while ret:
    key = cv2.waitKey(1)
    # exit on 'q' 'esc' 'Q'
    if key in [27, ord('Q'), ord('q')]: 
        break
    # resize the captured frame for face detection to increase processing speed
    resized_frame = cv2.resize(frame, frame_scale)

    processed_frame = resized_frame
    # Skip a frame if the no face was found last frame
    if frame_skip_rate == 0:
        faceFound = False
        for rotation in current_rotation_map:

            rotated_frame = ndimage.rotate(resized_frame, rotation)

            gray = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2GRAY)

            # return tuple is empty, ndarray if detected face
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(30, 30),
                #flags=cv2.cv.CV_HAAR_SCALE_IMAGE
            ) 

            # If frontal face detector failed, use profileface detector
            faces = faces if len(faces) else sideFace_cascade.detectMultiScale(                
                gray,
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(30, 30),
                #flags=cv2.cv.CV_HAAR_SCALE_IMAGE
            )

            # for f in faces:
            #     x, y, w, h = [ v*SCALE_FACTOR for v in f ] # scale the bounding box back to original frame size
            #     cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0))
            #     cv2.putText(frame, "Training Face", (x,y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0))

            if len(faces):
                for f in faces:
                    x, y, w, h = [ v for v in f ] # scale the bounding box back to original frame size
                    cropped_face = rotated_frame[y: y + h, x: x + w]   # img[y: y + h, x: x + w]
                    cropped_face = cv2.resize(cropped_face, FACE_DIM, interpolation = cv2.INTER_AREA)
                    cv2.rectangle(rotated_frame, (x,y), (x+w,y+h), (0,255,0))
                    cv2.putText(rotated_frame, "Training Face", (x,y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0))

                # rotate the frame back and trim the black paddings
                processed_frame = ut.trim(ut.rotate_image(rotated_frame, rotation * (-1)), frame_scale)

                # reset the optmized rotation map
                current_rotation_map = get_rotation_map(rotation)

                faceFound = True


                break

        if faceFound: 
            frame_skip_rate = 0
            # print "Face Found"
        else:
            frame_skip_rate = SKIP_FRAME
            # print "Face Not Found"

    else:
        frame_skip_rate -= 1
        # print "Face Not Found"


  
    cv2.putText(processed_frame, "Press ESC or 'q' to quit.", (5, 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255))

    cv2.imshow("Real Time Facial Recognition", processed_frame)



    if len(cropped_face):
        cv2.imshow("Cropped Face", cv2.cvtColor(cropped_face, cv2.COLOR_BGR2GRAY))
        if num_of_face_saved < num_of_face_to_collect and key == ord('p'):
            face_to_save = cv2.resize(cropped_face, (50, 50), interpolation = cv2.INTER_AREA)
            face_name = profile_folder_path+str(num_of_face_saved)+".png"
            cv2.imwrite(face_name, face_to_save)
            print "Pic Saved: ", face_name
            num_of_face_saved += 1

    # get next frame
    ret, frame = webcam.read()


webcam.release()
cv2.destroyAllWindows()
