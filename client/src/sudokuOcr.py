import cv2
import numpy as np


class OCRmodelClass:
    def __init__(self):
        samples = np.loadtxt('generalsamples.data', np.float32)
        responses = np.loadtxt('generalresponses.data', np.float32)
        responses = responses.reshape((responses.size, 1))

        self.model = cv2.KNearest()
        self.model.train(samples, responses)

        # jaki rodzaj morfologii bedzie uzywany
        self.iterations = [-1, 0, 1, 2]
        self.lvl = 0  # indeks iteracji
        self.iter = 0

        # odkomentowac w przypadku uzycia virtualImage
        self.original = np.zeros((9, 9), np.uint8)

        self.current = None

    def OCR(self, image):
        gray = cv2.cvtColor(image.output, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        image.outputGray = gray
        # proby OCR celem dobrania najelspzej metody
        self.success = [0, 0, 0, 0]
        self.errors = [0, 0, 0, 0]
        for self.lvl in self.iterations:
            image.output = np.copy(image.outputBackup)
            self.OCR_read(image)

        best = 9
        # ibest=-1
        for i in range(4):
            if self.success[i] > best and self.errors[i] >= 0:
                best = self.success[i]
                ibest = i

        print "najlepszy rodzaj morfologii: ", self.iterations[ibest]
        print (ibest)
        image.output = np.copy(image.outputBackup)
        self.lvl = self.iterations[ibest]
        self.OCR_read(image)
        self.original = self.current
        return self.current

    def OCR_read(self, image):
        self.iter += 1
        print (self.iter)
        # perform actual OCR using kNearest model
        thresh = cv2.adaptiveThreshold(image.outputGray, 255, 1, 1, 7, 2)
        if self.lvl >= 0:
            morph = cv2.morphologyEx(thresh, cv2.MORPH_ERODE, None, iterations=self.lvl)
        elif self.lvl == -1:
            morph = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, None, iterations=1)

        thresh_copy = morph.copy()
        # thresh2 changes after findContours
        contours, hierarchy = cv2.findContours(morph, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        thresh = thresh_copy

        self.current = np.zeros((9, 9), np.uint8)

        # testing section
        for cnt in contours:
            if cv2.contourArea(cnt) > 20:
                [x, y, w, h] = cv2.boundingRect(cnt)
                if h > 20 and h < 40 and w > 8 and w < 40:
                    if w < 20:
                        diff = 20 - w
                        x -= diff / 2
                        w += diff
                    sudox = x / 50
                    sudoy = y / 50
                    cv2.rectangle(image.output, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    # prepare region of interest for OCR kNearest model
                    roi = thresh[y:y + h, x:x + w]
                    roismall = cv2.resize(roi, (25, 35))
                    roismall = roismall.reshape((1, 875))
                    roismall = np.float32(roismall)
                    # find result
                    retval, results, neigh_resp, dists = self.model.find_nearest(roismall, k=1)

                    # check for read errors
                    if results[0][0] != 0:
                        string = str(int((results[0][0])))
                        if self.current[sudoy, sudox] == 0:
                            self.current[sudoy, sudox] = int(string)
                        else:
                            self.errors[self.lvl + 1] = -2
                        self.success[self.lvl + 1] += 1
                        cv2.putText(image.output, string, (x, y + h), 0, 1.4, (255, 0, 0), 3)
                    else:
                        self.errors[self.lvl + 1] = -3  # read zero error
                    cv2.imwrite('img/afterOcr.jpg', image.output)
