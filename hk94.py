import cv2
cap = cv2.VideoCapture("rtsp://admin:admin123@192.168.108.94//Streaming/Channels/1")
#cap = cv2.VideoCapture("rtsp://admin:admin123@192.168.108.91:554")
# 1是子码流,0是主码流
fps = cap.get(cv2.CAP_PROP_FPS)
print(fps)
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
print(size)
tot = 1
c = 1
while cap.isOpened():
    ret, frame = cap.read()
    cv2.namedWindow("hkcam",0)
    cv2.resizeWindow("hkcam",640,480)
    cv2.imshow("hkcam",frame)
    if tot % 10 == 0 :
        #cv2.imwrite('cut_{}.jpg'.format(c),frame)
        c = c + 1
    tot = tot + 1
    cv2.waitKey(1)
cap.release()
cv2.destroyAllWindows()