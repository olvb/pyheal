#!/usr/bin/env python3
import pyheal
import cv2
import os

for file in os.scandir('samples/'):
    if not file.name.endswith('_in.png'):
        continue

    img_name = file.name[:-len('_in.png')]

    in_path = 'samples/' + img_name + '_in.png'
    mask_path = 'samples/' + img_name + '_mask.png'
    out_path = 'samples/' + img_name + '_out.png'
    cv_path = 'samples/' + img_name + '_opencv.png'

    in_img = cv2.imread(in_path)
    mask_img = cv2.imread(mask_path)
    mask = mask_img[:, :, 0].astype(bool, copy=False)
    out_img = in_img.copy()

    pyheal.inpaint(out_img, mask, 5)
    cv2.imwrite(out_path, out_img)

    cv_img = cv2.inpaint(in_img, mask_img[:, :, 0], 5, cv2.INPAINT_TELEA)
    cv2.imwrite(cv_path, cv_img)
