#!/usr/bin/env python3
import argparse
import pyheal
import imageio

parser = argparse.ArgumentParser()
parser.add_argument('in_path', metavar='input_img', type=str,
	 				help='path to input image')
parser.add_argument('mask_path', metavar='mask_img', type=str,
					help='path to mask image')
parser.add_argument('out_path', metavar='ouput_img', type=str,
					help='path to output image')
parser.add_argument('-r', '--radius', metavar='R', nargs=1, type=int, default=[5],
					help='neighborhood radius')

args = parser.parse_args()

img = imageio.imread(args.in_path)
mask_img = imageio.imread(args.mask_path)
mask = mask_img[:, :, 0].astype(bool, copy=False)
pyheal.inpaint(img, mask, args.radius[0])
imageio.imwrite(args.out_path, img)
