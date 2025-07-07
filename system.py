import cv2
cap = cv2.VideoCapture(1)
ret, frame = cap.read()
if ret:
	cv2.imwrite('/tmp/test_image.jpg',frame)
cap.release()
