import cv2
import zmq
import _thread
import base64
from skimage.filters import threshold_otsu
import config as CONFIG
import pickle


def configure_port():
    context = zmq.Context()
    # recieve work
    receiverSocket = context.socket(zmq.PULL)
    receiverSocket.connect("tcp://127.0.0.1:%s" % CONFIG.PRODUCER_SENDER_PORT)
    # send work
    senderSocket = context.socket(zmq.PUSH)
    senderSocket.connect("tcp://127.0.0.1:%s" % CONFIG.CONSUMER1_SENDER_PORT)

    return senderSocket, receiverSocket


def apply_threshold(image):
    thresh = threshold_otsu(image)
    binary = image <= thresh
    return binary


def msg_to_image(message):
    message = pickle.loads(message)
    frameNum = message["frameNum"]
    image = message["img"]
    image = bytearray(base64.b64decode(image))
    return frameNum, image


def image_to_msg(frameNum, frame):
    imgToString = base64.b64encode(frame)
    msgD = {"frameNum": frameNum, "img": imgToString}
    msg = pickle.dumps(msgD)
    return msg



def thread_function(senderSocket, receiverSocket):
    while True:
        message = receiverSocket.recv()
        frameNum, image = msg_to_image(message)
        binaryImage = apply_threshold(image)
        senderSocket.send_json(image_to_msg(frameNum, binaryImage))


# Create N threads as follows
try:
    threadCount = CONFIG.N
    senderSocket, receiverSocket = configure_port()
    while threadCount:
        _thread.start_new_thread(
            thread_function, (senderSocket, receiverSocket))
        threadCount -= 1
except:
    print("Error: unable to start threading")