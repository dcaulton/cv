import cv2
import datetime
import os
import re
import sys

nonzero_threshold_upper = 1000    # more than this, it's just spots of noise in the frame
nonzero_threshold_lower = 12  # more than this, nothing is in the frame
feature_threshold_lower = 7  # less than this, the feature is too small
pixel_brightness_threshold = 50
reference_scene_offset = (0,0)
working_dir = '/home/pi/cv/pics'
stream_url = 'http://127.0.0.1:8086'
stream_filename = os.path.join(working_dir, 'index.html')
latest_frame_filename = os.path.join(working_dir, 'current_frame.jpg')
latest_frame_homed_filename = os.path.join(working_dir, 'current_frame_homed.jpg')
last10_filename = os.path.join(working_dir, 'last10_image.jpg')
diff_filename = os.path.join(working_dir, 'difference.jpg')
bwdiff_filename = os.path.join(working_dir, 'bw_difference.jpg')
bwdiffthresh_filename = os.path.join(working_dir, 'bw_difference_thresh.jpg')
blurred_filename = os.path.join(working_dir, 'blurred.jpg')
edged_filename = os.path.join(working_dir, 'edged.jpg')
features_filename = os.path.join(working_dir, 'features.jpg')

def get_last_10_images():
    # allow for an override if there is something in the last 10 images you want to ignore.
    # keep a list of scenes with nothing in them.  find which one is closest to last_10, minus
    #   the feature it has
    jj = os.path.join(working_dir, 'xxy')
    tc = 'rm -rf {0}; mkdir {1}; cd /home/pi/Pictures; ls -t | grep "\-00.jpg\|\-01.jpg\|\-snapshot.jpg" | head -10 | xargs cp -t {2}; convert -average {3}/*.jpg {4}'.format(jj, jj, jj, jj, last10_filename)
    os.system(tc)

def save_stream_to_a_file():
    os.system('timeout 2 wget -q {0} -O {1}'.format(stream_url, stream_filename))
    print 'stream saved'

def parse_image_from_stream():
    boundary_re = re.compile('--BoundaryString')
    ifh = open(stream_filename, 'r')
    ofh = open(latest_frame_filename, 'wb')
    line = ifh.readline()
    if boundary_re.match(line):
        print 'found starting boundary'
        line = ifh.readline() #Content-type: image/jpeg\r\n
        line = ifh.readline() # Content-Length:        1985\r\n
        line = ifh.readline() #   (empty line)

        max_loops = 10000
        count = 0
        while True:
            count += 1
            if count > max_loops:
                print 'max loops parsing image from stream'
                break
            line = ifh.readline() 
            if boundary_re.match(line):
                print 'found ending boundary'
                ofh.close()
                return
            else:
                ofh.write(line)
    else:
        print 'could not find a boundary line'

def image_differences():
    # image diff in RGB space
    last10 = cv2.imread(last10_filename)
    latest = cv2.imread(latest_frame_filename)
    diff = cv2.subtract(latest, last10)
    cv2.imwrite(diff_filename, diff)

    # extract just the G portion of the diff, block out timestamp, save as grayscale
    (B, bwdiff, R) = cv2.split(diff)
    cv2.rectangle(bwdiff, (0,50), (80,60), (0,0,0), -1)
    cv2.imwrite(bwdiff_filename, bwdiff)

    # apply a threshold to the grayscale, save as b&w
    # for now I am getting away with a single brightnexx threshold.  The way it really works though
    #  is that if you're far away or a small cat, you might make the room less blue, more yellow,
    #  but you'd still be detectable as being more yellow.  If you're big or close to the camera
    #  the room is very blue and you will be a brighter yellow
    (T, bwdiffthresh) = cv2.threshold(bwdiff, pixel_brightness_threshold, 255, cv2.THRESH_BINARY)
    cv2.imwrite(bwdiffthresh_filename, bwdiffthresh)

    # count white pixels, compare to 'empty room' threshold
    #  (empty room is mostly yellow, when there is a person in the room, they
    #   become the hot and everything else becomes less yellow=less green channel)
    nonzero_pixel_count = cv2.countNonZero(bwdiffthresh)
    if (nonzero_pixel_count < nonzero_threshold_upper
        and nonzero_pixel_count > nonzero_threshold_lower):
        msg = 'looks like something changed and it is occupying the frame: {0} pixels changed'.format(nonzero_pixel_count)
        print msg
        return True
    else:
        msg = 'frame looks like the rolling average: {0} pixels changed'.format(nonzero_pixel_count)
        print msg
        return False

def find_features():
    # blur out noise
    diff_thresh = cv2.imread(bwdiffthresh_filename)
    blurred = cv2.medianBlur(diff_thresh, 3)
    cv2.imwrite(blurred_filename, blurred)
    # use canny edge detection to draw rings around the bounded objects
    edged = cv2.Canny(blurred, 30, 150)
    cv2.imwrite(edged_filename, edged)

    (_, cons, _) = cv2.findContours(edged,
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    # draw the contours over the original color difference image
    diff = cv2.imread(diff_filename)
    features = diff.copy()
    cv2.drawContours(features, cons, -1, (0,255,0), 2)
    cv2.imwrite(features_filename, features)

    if not cons:
        print 'no contours found'
    return cons

def filter_contours(contours):
    # try to prefilter contours.  If there is one that's big enough to be a 
    #   person, then there is one that looks like a reflection (same x, 
    #   only separated on y by 5 pixels or so), delete and don't report on
    #   the reflection as a separate entity
    #
    # remove_reflections
    # remove_too_small
    # remove_illogical_locations

def compare_contours_to_reference(cons):
    # list contours
    for c in cons:
        (x,y,w,h) = cv2.boundingRect(c)
        if w > feature_threshold_lower or h > feature_threshold_lower:
            print 'feature above threshold: x,y,w,h =({0},{1},{2},{3})'.format(x,y,w,h)
            home_scene_rect = (x+reference_scene_offset[0],
                               y+reference_scene_offset[1],
                               w,
                               h)
            if h > 2*w and h > 10:
                print 'its a standing person'
            if x > 40 and y > 30:
                print 'its in the BR quadrant'
            bottom_y = h + y
            if bottom_y < 30:
                print 'its in the far half of the room'
        else:
            print 'feature is below the lower threshold size'


try:
    get_last_10_images()
    save_stream_to_a_file()
    parse_image_from_stream()

    image_has_differences = image_differences()
    if image_has_differences:
        contours = find_features()
        filter_contours(contours)
        compare_contours_to_reference(contours)
except Exception, e:
    print e
