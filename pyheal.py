import numpy as np
from math import sqrt as sqrt
import heapq

# flags
KNOWN = 0
BAND = 1
UNKNOWN = 2
# extremity values
INF = 1e6 # dont use np.inf to avoid inf * 0
EPS = 1e-6

def _solve_eikonal(y1, x1, y2, x2, height, width, dists, flags):
    # check image frame
    if y1 < 0 or y1 >= height or x1 < 0 or x1 >= width:
        return INF
    
    if y2 < 0 or y2 >= height or x2 < 0 or x2 >= width:
        return INF

    flag1 = flags[y1, x1]
    flag2 = flags[y2, x2]

    # both pixels are known
    if flag1 == KNOWN and flag2 == KNOWN:
        dist1 = dists[y1, x1]
        dist2 = dists[y2, x2]
        d = 2.0 - (dist1 - dist2) ** 2
        if d > 0.0:
            r = sqrt(d)
            s = (dist1 + dist2 - r) / 2.0
            if s >= dist1 and s >= dist2:
                return s
            s += r
            if s >= dist1 and s >= dist2:
                return s
            # unsolvable
            return INF
    
    # only 1st pixel is known
    if flag1 == KNOWN:    
        dist1 = dists[y1, x1]
        return 1.0 + dist1

    # only 2d pixel is known
    if flag2 == KNOWN:
        dist2 = dists[y2, x2]
        return 1.0 + dist2

    # no pixel is known
    return INF

# returns gradient for one pixel, computed on 2 pixel range if possible
def _pixel_gradient(y, x, height, width, vals, flags):
    val = vals[y, x]

    # compute grad_y
    prev_y = y - 1
    next_y = y + 1
    if prev_y < 0 or next_y >= height:
        grad_y = INF
    else:
        flag_prev_y = flags[prev_y, x]
        flag_next_y = flags[next_y, x]

        if flag_prev_y != UNKNOWN and flag_next_y != UNKNOWN:
            grad_y = (vals[next_y, x] - vals[prev_y, x]) / 2.0
        elif flag_prev_y != UNKNOWN:
            grad_y = val - vals[prev_y, x]
        elif flag_next_y != UNKNOWN:
            grad_y = vals[next_y, x] - val
        else:
            grad_y = 0.0
    
    # compute grad_x
    prev_x = x - 1
    next_x = x + 1
    if prev_x < 0 or next_x >= width:
        grad_x = INF
    else:
        flag_prev_x = flags[y, prev_x]
        flag_next_x = flags[y, next_x]

        if flag_prev_x != UNKNOWN and flag_next_x != UNKNOWN:
                grad_x = (vals[y, next_x] - vals[y, prev_x]) / 2.0
        elif flag_prev_x != UNKNOWN:
                grad_x = val - vals[y, prev_x]
        elif flag_next_x != UNKNOWN:
            grad_x = vals[y, next_x] - val
        else:
            grad_x = 0.0

    return grad_y, grad_x

# compute distances between initial mask contour and pixels outside mask, using FMM (Fast Marching Method)
def _compute_outside_dists(height, width, dists, flags, band, radius):
    band = band.copy()
    orig_flags = flags
    flags = orig_flags.copy()
    # swap INSIDE / OUTSIDE
    flags[orig_flags == KNOWN] = UNKNOWN
    flags[orig_flags == UNKNOWN] = KNOWN

    last_dist = 0.0    
    double_radius = radius * 2
    while band:
        # reached radius limit, stop FFM
        if last_dist >= double_radius:
            break
    
        # pop BAND pixel closest to initial mask contour and flag it as KNOWN
        _, y, x = heapq.heappop(band)
        flags[y, x] = KNOWN

        # process immediate neighbors (top/bottom/left/right)
        neighbors = [(y - 1, x), (y, x - 1), (y + 1, x), (y, x + 1)]
        for nb_y, nb_x in neighbors:
            # skip out of frame
            if nb_y < 0 or nb_y >= height or nb_x < 0 or nb_x >= width:
                continue
    
            # neighbor already processed, nothing to do
            if flags[nb_y, nb_x] != UNKNOWN:
                continue
    
            # compute neighbor distance to inital mask contour
            last_dist = min([
                _solve_eikonal(nb_y - 1, nb_x, nb_y, nb_x - 1, height, width, dists, flags),
                _solve_eikonal(nb_y + 1, nb_x, nb_y, nb_x + 1, height, width, dists, flags),
                _solve_eikonal(nb_y - 1, nb_x, nb_y, nb_x + 1, height, width, dists, flags),
                _solve_eikonal(nb_y + 1, nb_x, nb_y, nb_x - 1, height, width, dists, flags)
            ])
            dists[nb_y, nb_x] = last_dist

            # add neighbor to narrow band            
            flags[nb_y, nb_x] = BAND
            heapq.heappush(band, (last_dist, nb_y, nb_x))

    # distances are opposite to actual FFM propagation direction, fix it
    dists *= -1.0

# computes pixels distances to initial mask contour, flags, and narrow band queue
def _init(height, width, mask, radius):
    # init all distances to infinity
    dists = np.full((height, width), INF, dtype=float)
    # status of each pixel, ie KNOWN, BAND or UNKNOWN
    flags = mask.astype(int) * UNKNOWN
    # narrow band, queue of contour pixels
    band = []

    mask_y, mask_x = mask.nonzero()
    for y, x in zip(mask_y, mask_x):        
        # look for BAND pixels in neighbors (top/bottom/left/right)
        neighbors = [(y - 1, x), (y, x - 1), (y + 1, x), (y, x + 1)]
        for nb_y, nb_x in neighbors:
            # neighbor out of frame
            if nb_y < 0 or nb_y >= height or nb_x < 0 or nb_x >= width:
                continue

            # neighbor already flagged as BAND
            if flags[nb_y, nb_x] == BAND:
                continue

            # neighbor out of mask => mask contour
            if mask[nb_y, nb_x] == 0:
                flags[nb_y, nb_x] = BAND
                dists[nb_y, nb_x] = 0.0
                heapq.heappush(band, (0.0, nb_y, nb_x))
    
    
    # compute distance to inital mask contour for KNOWN pixels
    # (by inverting mask/flags and running FFM)    
    _compute_outside_dists(height, width, dists, flags, band, radius)

    return dists, flags, band

# returns RGB values for pixel to by inpainted, computed for its neighborhood
def _inpaint_pixel(y, x, img, height, width, dists, flags, radius):
    dist = dists[y, x]
    # normal to pixel, ie direction of propagation of the FFM
    dist_grad_y, dist_grad_x = _pixel_gradient(y, x, height, width, dists, flags)
    pixel_vals = np.zeros((3), dtype=float)
    weight_sum = 0.0

    # iterate on each pixel in neighborhood (nb stands for neighbor)
    for nb_y in range(y - radius, y + radius + 1):
        #  pixel out of frame
        if nb_y < 0 or nb_y >= height:
            continue
        
        for nb_x in range(x - radius, x + radius + 1):
            # pixel out of frame
            if nb_x < 0 or nb_x >= width:
                continue
            
            # skip unknown pixels (including pixel being inpainted)
            if flags[nb_y, nb_x] == UNKNOWN:
                continue
            
            # vector from point to neighbor
            dir_y = y - nb_y
            dir_x = x - nb_x
            dir_length_square = dir_y ** 2 + dir_x ** 2
            dir_length = sqrt(dir_length_square)
            # pixel out of neighborhood
            if dir_length > radius:
                continue

            # compute weight
            # neighbor has same direction gradient => contributes more
            dir_factor = abs(dir_y * dist_grad_y + dir_x * dist_grad_x)
            if dir_factor == 0.0:
                dir_factor = EPS

            # neighbor has same contour distance => contributes more
            nb_dist = dists[nb_y, nb_x]
            level_factor = 1.0 / (1.0 + abs(nb_dist - dist))

            # neighbor is distant => contributes less
            dist_factor = 1.0 / (dir_length * dir_length_square)

            weight = abs(dir_factor * dist_factor * level_factor)

            pixel_vals[0] += weight * img[nb_y, nb_x, 0]
            pixel_vals[1] += weight * img[nb_y, nb_x, 1]
            pixel_vals[2] += weight * img[nb_y, nb_x, 2]

            weight_sum += weight

    pixel_vals /= weight_sum
    return pixel_vals

# main inpainting function
def inpaint(img, mask, radius=5):
    if img.shape[0:2] != mask.shape[0:2]:
        error('Image and mask dimensions do not match')

    height, width = img.shape[0:2]
    dists, flags, band = _init(height, width, mask, radius)

    # find next pixel to inpaint with FFM (Fast Marching Method)
    # FFM advances the band of the mask towards its center,
    # by sorting the area pixels by their distance to the initial contour
    while band:
        # pop band pixel closest to initial mask contour
        _, y, x = heapq.heappop(band)
        # flag it as KNOWN
        flags[y, x] = KNOWN

        # process his immediate neighbors (top/bottom/left/right)
        neighbors = [(y - 1, x), (y, x - 1), (y + 1, x), (y, x + 1)]
        for nb_y, nb_x in neighbors:
            # pixel out of frame
            if nb_y < 0 or nb_y >= height or nb_x < 0 or nb_x >= width:
                continue

            # neighbor outside of initial mask or already processed, nothing to do
            if flags[nb_y, nb_x] != UNKNOWN:
                continue

            # compute neighbor distance to inital mask contour
            nb_dist = min([
                _solve_eikonal(nb_y - 1, nb_x, nb_y, nb_x - 1, height, width, dists, flags),
                _solve_eikonal(nb_y + 1, nb_x, nb_y, nb_x + 1, height, width, dists, flags),
                _solve_eikonal(nb_y - 1, nb_x, nb_y, nb_x + 1, height, width, dists, flags),
                _solve_eikonal(nb_y + 1, nb_x, nb_y, nb_x - 1, height, width, dists, flags)
            ])
            dists[nb_y, nb_x] = nb_dist

            # inpaint neighbor
            pixel_vals = _inpaint_pixel(nb_y, nb_x, img, height, width, dists, flags, radius)

            img[nb_y, nb_x, 0] = pixel_vals[0]
            img[nb_y, nb_x, 1] = pixel_vals[1]
            img[nb_y, nb_x, 2] = pixel_vals[2]

            # add neighbor to narrow band
            flags[nb_y, nb_x] = BAND
            # push neighbor on band
            heapq.heappush(band, (nb_dist, nb_y, nb_x))