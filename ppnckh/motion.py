from fer import FER
from mtcnn import MTCNN
import cv2

default_expanded_size = 10


def add_size(input_size, max_size):
    new_size = input_size + default_expanded_size
    return input_size if new_size > max_size else new_size


def remove_size(input_size):
    new_size = input_size - default_expanded_size
    return input_size if new_size < 0 else new_size


img = cv2.imread("smile.jpg")
max_height = img.shape[0]
max_width = img.shape[1]
face_detector = MTCNN()
emotion_detector = FER()
faces = face_detector.detect_faces(img)

for face in faces:
    x, y, w, h = face['box']
    face_img = img[remove_size(y): add_size(y + h, max_height), remove_size(x): add_size(x + w, max_width)]

    emotion_detector.detect_emotions(face_img)
    emotion, score = emotion_detector.top_emotion(face_img)
    print(emotion)


def get_emotion(img):
    #TODO: read img, return emotion
    return emotion