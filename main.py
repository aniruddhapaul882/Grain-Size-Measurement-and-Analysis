import cv2
from scipy import ndimage
from skimage import color, measure
import paho.mqtt.client as mqtt
import time
import requests
import multiprocessing


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Client is connected")
        global connected
        connected = True
    else:
        print("Client is not connected")


cap = cv2.VideoCapture('rtsp://*****:**********@************:554/Streaming/Channels/101?transportmode=unicast&profile=Profile_1') # This is to take camera feed using RTSP, for webcam/USBcam try "0" or "1"
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
# sub = cv2.createBackgroundSubtractorMOG2(500, 255, detectShadows=False)
sub2 = cv2.bgsegm.createBackgroundSubtractorGMG()
sub3 = cv2.createBackgroundSubtractorKNN(1, 0, detectShadows=False)
s = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
connected = False
message_recieved = False

broker_add = "***.***.**.***"
port = ****
user = "userName"
password = "password"
client = mqtt.Client("MQTT")
client.username_pw_set(user, password)
client.on_connect = on_connect
client.connect(broker_add, port)
client.loop_start()
OUTR1 = 0
OUTR2 = 0
INR = 0
ctr = 0


def on_message(client, userdata, message):
    print("Message Recieved" + str(message.payload.decode("utf-8")))


while connected != True:
    time.sleep(0.2)

x, y, h, w = 0, 0, 1381, 1078

while True:
    INRP = 0
    OUTR1P = 0
    OUTR2P = 0
    success, img1 = cap.read()
    # img = img1[y:y+h, x:x+w]
    if not success:
        print("unable to capture stream")
        continue
    else:
        ctr += 1
        # imgR = cv2.resize(img, (640, 480))
        sub_mask0 = sub3.apply(img1)
        print(ndimage.sum_labels(sub_mask0))
        if ndimage.sum_labels(sub_mask0) <= 8000:
            break
        else:
            pass
        sub_mask = cv2.morphologyEx(sub_mask0, cv2.MORPH_RECT, kernel)
        label_mask, num_lables = ndimage.label(sub_mask, s)
        img2 = color.label2rgb(label_mask, bg_label=0)
        clusters = measure.regionprops(label_mask, img1)
        for props in clusters:
            size = props.perimeter / (22 / 7)
            size = size * 0.8985 #pixel to distance ratio
            if 45 <= size <= 60: # measurement level 1
                INR += 1
            elif 30 < size <= 45: # measurement level 2
                OUTR1 += 1
            elif 60 <= size <= 80: # measurement level 3
                OUTR2 += 1
        SUM = INR + OUTR1 + OUTR2
        if SUM > 0:
            INRP = (INR / SUM) * 100
            OUTR1P = (OUTR1 / SUM) * 100
            OUTR2P = (OUTR2 / SUM) * 100

        if INRP == 0 and OUTR1P == 0 and OUTR2P == 0:
            client.publish("AdvertisementTopic1", "NO DATA", 2)
            print("Null Sent")
        else:
            if ctr == 20:
                client.publish("AdvertisementTopic2", str(round(INRP, 2)) + "/" + str(round(OUTR1P, 2)) + "/" + str(round(OUTR2P, 2)), 2)
                print("Publish Successful")
                print(str(round(INRP, 2)) + "/" + str(round(OUTR1P, 2)) + "/" + str(round(OUTR2P, 2)))
                break
        # cv2.imshow("a", imgR)
        # cv2.imshow("b", sub_mask0)
        cv2.imshow("c", img2)
        INR = 0
        OUTR1 = 0
        OUTR2 = 0

        if cv2.waitKey(100) == 13:
            break

client.loop_stop()
cap.release()
cv2.destroyAllWindows()
