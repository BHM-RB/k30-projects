import cv2
import matplotlib.pyplot as plt

img = cv2.imread('smile.jpg')
height, width, channels = img.shape

new_w = int(width/3)
# imgplot = plt.imshow(cv2.cvtColor(img[0:height, 0:new_w], cv2.COLOR_BGR2RGB))
# plt.show()
# imgplot = plt.imshow(cv2.cvtColor(img[0:height, new_w:new_w*2], cv2.COLOR_BGR2RGB))
# plt.show()
# imgplot = plt.imshow(cv2.cvtColor(img[0:height, new_w*2:new_w*3], cv2.COLOR_BGR2RGB))
# plt.show()
cv2.imwrite('1.png', img[0:height, 0:new_w])
cv2.imwrite('2.png', img[0:height, new_w:new_w*2])
cv2.imwrite('3.png', img[0:height, new_w*2:new_w*3])

hsv1 = cv2.cvtColor(img[0:height, 0:new_w], cv2.COLOR_BGR2HSV)
print(int(hsv1[..., 2].mean()/255*127))

hsv1 = cv2.cvtColor(img[0:height, new_w:new_w*2], cv2.COLOR_BGR2HSV)
print(int(hsv1[..., 2].mean()/255*127))

hsv1 = cv2.cvtColor(img[0:height, new_w*2:new_w*3], cv2.COLOR_BGR2HSV)
print(int(hsv1[..., 2].mean()/255*127))