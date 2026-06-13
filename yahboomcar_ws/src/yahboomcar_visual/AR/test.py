import numpy as np
import cv2
 
cap = cv2.VideoCapture(0)

with np.load('B.npz') as X:
    mtx, dist, _, _ = [X[i] for i in ('mtx', 'dist', 'rvecs', 'tvecs')]
 
 
# »­×ø±êÖá
def draw(img, corners, imgpts):
    corner = tuple(corners[0].ravel())
    img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255, 0, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0, 255, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0, 0, 255), 5)
    return img
 
 
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
objp = np.zeros((6*6, 3), np.float32)
objp[:, :2] = np.mgrid[0:6, 0:6].T.reshape(-1, 2)
axis = np.float32([[3, 0, 0], [0, 3, 0], [0, 0, -3]]).reshape(-1, 3)
 
 
if cap.isOpened() is True:  # ¼ì²éÉãÏñÍ·ÊÇ·ñÕý³£Æô¶¯
    while(1):
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (6, 6), None)
        if not ret:
            cv2.imshow('img', img)
        else:
            corners2 = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria)
            # Find the rotation and translation vectors.
            ret, rvecs, tvecs = cv2.solvePnP(objp, corners2, mtx, dist)
            # project 3D points to image plane
            imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, mtx, dist)
            img = draw(img, corners2, imgpts)
            cv2.imshow('img', img)
        k = cv2.waitKey(5) & 0xFF
        if k == ord('s'):
            cv2.imwrite('AXIS'+'.png', img)
        elif k == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
else:
    print('cap is not opened!')
