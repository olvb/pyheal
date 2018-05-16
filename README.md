# FMM Inpainting

[Alexander Telea's algorithm][1] uses the Fast Marching Method (FFM) to construct and maintain a list of the pixels forming the contour of area to inpaint. This area is progressively shrinked while pixels are processed until none remain to be inpainted. Pixels are handled starting from the initial contour, then going closer towards the center of the area to inpaint, as the contour itself is tightened.

[1]: https://www.rug.nl/research/portal/files/14404904/2004JGraphToolsTelea.pdf

FFM only helps with the order in which pixels are processed, but does not determine how each pixel is going to be actually inpainted. Telea performs a weighted average of all pixels in the neighborhood of the inpainted pixel. The neighborhood is determined by a radius, which value should be close to the thickness of the area to inpainted. The weight function depends on the following factors:
- the distance between a pixel and it neighbors, ie closers neighbors contribute more;
- the level set distance to the original contour, ie neighbors on the same level set (or iso line) contribute more;
- the colinearity of the vector from a pixel to its neighbors and the FFM direction of propagation. This factor will have the effect of extending isophotes (ie lines) reaching the area to inpaint, by giving more weight to neighbors when they are in the axis going from the inpainting pixel in the direction of the FFM.

# Implementations details

Our implementation borrows from different source codes, including the [OpenCV C++ implementation][1] and [Telea's implementation][2] itself. As advised in the original paper, we first run a FFM in order to compute distances between pixels outside of the mask and the initial mask contour, before running the main FFM that performs the actual inpainting.

[1]: https://github.com/opencv/opencv/blob/master/modules/photo/src/inpaint.cpp
[2]: https://github.com/erich666/jgt-code/tree/master/Volume_09/Number_1/Telea2004/AFMM_Inpainting

Despite closely following the same algorithm, our Python version is considerably slower than the mentioned implementations. In order to keep the processing time under a reasonable amount, we have chosen to only compute the weighted average previously described, dropping the average gradient that is also mentioned in the article and applied in most implementations. This allows for a x6 speed gain while maintaining "good-enough" results, albeit not as smooth.

# Results

Click for full-scale image

| Initial image               | Pyheal                        | OpenCV                      |
| :-------------------------: | :---------------------------: | :-------------------------: |
| [![][im1_in_thumb]][im1_in] | [![][im1_out_thumb]][im1_out] | [![][im1_cv_thumb]][im1_cv] |

[im1_in]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_in.png
[im1_in_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_in.png
[im1_out]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_out.png
[im1_out_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_out.png
[im1_cv]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_opencv.png
[im1_cv_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/tulips_opencv.png

| Initial image               | Pyheal                        | OpenCV                      |
| :-------------------------: | :---------------------------: | :-------------------------: |
| [![][im2_in_thumb]][im2_in] | [![][im2_out_thumb]][im2_out] | [![][im2_cv_thumb]][im2_cv] |

[im2_in]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_in.png
[im2_in_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_in.png
[im2_out]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_out.png
[im2_out_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_out.png
[im2_cv]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_opencv.png
[im2_cv_thumb]: https://raw.githubusercontent.com/olvb/pyheal/master/samples/lena_opencv.png

*Samples images from https://homepages.cae.wisc.edu/~ece533/images/*

The Telea algorithm gives satisfying results for narrow masks. One of its niceties is that it can be directly applied with masks containing non-contiguous regions, without any additional code.
When used with larger masks or on textured or patterned images, its half-blurring half-stretching effect will however become apparent.
