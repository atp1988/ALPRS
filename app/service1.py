import cv2
import numpy as np
import os
import torch
from datetime import datetime
from boxes import Box
from crnn_recogition import CRNNInferenceTorch
from skimage.metrics import structural_similarity as ssim

class Inference:
    def __init__(self, yolo_path, recog_path):
        # self.detector = torch.hub.load('ultralytics/yolov5', 'custom', path=yolo_path)
        self.detector = torch.hub.load('yolov5', 'custom', source='local', path=yolo_path)
        self.recognizer = CRNNInferenceTorch(recog_path, device='cpu')
        self.path_orig = 'original-plate'
        self.path_crop = 'cropped-plate'

    # write a method for resizing the image
    @staticmethod
    def resize_image(img, width, height):
        resized_image = cv2.resize(img, (width, height))
        return resized_image

    @staticmethod
    def preprocessing(img, width, height) -> np.ndarray:
        if type(img) is not np.ndarray:
            img = np.array(img).astype(np.uint8)
        img = Inference.resize_image(img, width, height)
        img = img[..., ::-1]  # BGR to RGB
        return img
    
    @staticmethod
    def calculate_ssim(img1, img2):
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        print (ssim(gray1, gray2))
        return ssim(gray1, gray2)

    # @staticmethod
    def load_last_saved_frames(self, image, count=40):
        files = sorted([os.path.join(self.path_orig, f) for f in os.listdir(self.path_orig) if f.endswith('.jpg')],
                    key=lambda x: os.path.getmtime(x), reverse=True)
        # if len(files) == 0:
        #     filename = "{'no_object'}_" + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
        #     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #     cv2.imwrite(os.path.join(self.path_orig, filename), image)
        #     return
        images = [cv2.imread(f) for f in files[:len(files)]]

        # Check similarity
        is_similar = False
        for image_array in images:
            if image_array is not None:
                similarity = self.calculate_ssim(image_array, image)
                if similarity > 0.90:  # Threshold for similarity
                    is_similar = True
                    break

        # Save frame if not similar
        if not is_similar:
            filename = "{'no_object'}_" + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            cv2.imwrite(os.path.join(self.path_orig, filename), image)

    
    def infer(self, image, width, height):
        img = self.preprocessing(image, width, height)
        plates = {}
        objects = self.detector(img)
        boxes = objects.pandas().xyxy[0].values[:, :4]
        if len(boxes):
            results = []
            for box in boxes:
                img_part = Box.get_box_img(img, (box[1], box[0], box[3], box[2]))
                result = self.recognizer.infer(img_part)
                results.append(result)
            i = 1
            for res, box in zip(results, boxes):
                if len(res) == 8:
                    plate_data = {
                            "plate_part1": res[:2],
                            "plate_part2": res[2:3],
                            "plate_part3": res[3:6],
                            "plate_part4": res[6:]
                        }
                    plates[f"plate_{i}"] = plate_data
                    i += 1
                 
                    # save croped plate
                    plate_str = plate_data['plate_part1'] + plate_data['plate_part2'] + plate_data['plate_part3'] + plate_data['plate_part4'] + '.jpg'
                    crop_img_path = os.path.join(self.path_crop, plate_str)
                    img_part = cv2.cvtColor(img_part, cv2.COLOR_BGR2RGB)
                    cv2.imwrite(crop_img_path, img_part)
                     # save orig plate
                    cv2.imwrite(os.path.join(self.path_orig, plate_str), image)

                else:                   
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if res not in os.listdir(self.path_crop):
                        filename = f"{'no_ocr'}_{res}_{timestamp}'.jpg'"
                        crop_img_path = os.path.join(self.path_crop, filename)
                        img_part = cv2.cvtColor(img_part, cv2.COLOR_BGR2RGB)
                        cv2.imwrite(crop_img_path, img_part)                 
                
        else:
            # plates["plate"] = {
            #     "plate_part1": None,
            #     "plate_part2": None,
            #     "plate_part3": None,
            #     "plate_part4": None
            # }
            plates[f"plate"] = None
            self.load_last_saved_frames(image)
        return plates
