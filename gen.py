import os

a = open("train.txt", "a+")
for path, subdirs, files in os.walk('/home/dung/Downloads/keras-yolo3-master/dataset/Tomato_1'):
   for filename in files:
      a.write("/home/dung/Downloads/keras-yolo3-master/dataset/Tomato_1/"+filename+" 0,0,100,100,0"+ os.linesep)
