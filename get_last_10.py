import cv2
import os
import datetime
import numpy as np
import re

the_source_dir = '/home/pi/Pictures'
the_output_dir = '/home/pi/Pictures'

def sorted_ls(path):
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))


class GetLast10(object):
    # averages the most recent 10 snapshot images that are sitting in the /home/pi/Pictures dir

    @staticmethod
    def get_last_10_images(source_dir, output_dir):
        # allow for an override if there is something in the last 10 images you want to ignore.
        # keep a list of scenes with nothing in them.  find which one is closest to last_10, minus
        #   the feature it has
        output_name = os.path.join(
            output_dir,
            "last10_{0}.jpg".format(datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S')))
        silly_output_name = os.path.join(output_dir,'wocka_wocka.jpg')

        st = sorted_ls(source_dir)
        tf = [x for x in st if re.findall('-snapshot\.jpg$', x)]
        tfl10 = tf[-10:]
        
        print 'last 10 eligible pics are ' + str(tfl10)
        input_image_array = []

        for p in tfl10:
            f = os.path.join(source_dir, p)
            pi = cv2.imread(f)
            input_image_array.append(pi)

        canvas = .1 * input_image_array[0]
        for im in input_image_array[1:]:
            canvas = cv2.add(canvas, im*.1)
        cv2.imwrite(output_name, canvas.astype(int))
            
        return output_name

def main():
    try:
        output_name = GetLast10.get_last_10_images(the_source_dir, the_output_dir)
        print 'created ' + output_name
    except Exception, e:
        print 'get_last_10 had an exception'
        print e

if __name__ == "__main__":
    main()
