from feature_extractor2 import NaiveDlib
import cv2
import numpy as np  # 添加模块和矩阵模块

cap = cv2.VideoCapture(0)
#cap1 = cv2.VideoCapture(1)
naivedlib = NaiveDlib()
# 打开摄像头，若打开本地视频，同opencv一样，只需将０换成("×××.avi")
while (1):  # get a frame
    ret, frame = cap.read()  # show a frame
    #ret1, frame1 = cap1.read()
    image = frame.copy()
    #width = int(image.shape[1] / 2)
    #height = int(image.shape[0] / 2)
    #image3 = cv2.resize(image.copy(), (width, height))
    try:
        bbox = naivedlib.getLargestFaceBoundingBox(image)
        frame = naivedlib.drawbbox(image, bbox)
    except:
        frame = image.copy()
    #cv2.imshow("capture1",frame1)
    cv2.imshow("capture", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
#cap1.release()
cv2.destroyAllWindows()
# 释放并销毁窗口