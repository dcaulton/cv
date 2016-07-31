#! /usr/bin/python
# grabs a single frame from a ffmpeg web stream
import datetime
import os
import re
import sys

working_dir = '/home/pi/cv/pics'
stream_url = 'http://127.0.0.1:8086'
stream_filename = os.path.join(working_dir, 'index.html')
frame_filename = os.path.join(working_dir, 'current_frame.jpg')

def get_last_10_images():
    jj = os.path.join(working_dir, 'xxy')
    fn10 = os.path.join(working_dir, 'last10_image.jpg')
    tc = 'rm -rf {0}; mkdir {1}; cd /home/pi/Pictures; ls -t | grep "\-00.jpg\|\-01.jpg\|\-snapshot.jpg" | head -10 | xargs cp -t {2}; convert -average {3}/*.jpg {4}'.format(jj, jj, jj, jj, fn10)
    print tc
    os.system(tc)

def save_stream_to_a_file():
    os.system('timeout 2 wget {0} -O {1}'.format(stream_url, stream_filename))
    print 'stream saved'

def parse_image_lines():
    boundary_re = re.compile('--BoundaryString')
    ifh = open(stream_filename, 'r')
    ofh = open(frame_filename, 'wb')
    line = ifh.readline()
    if boundary_re.match(line):
        print 'found starting boundary'
        line = ifh.readline() #Content-type: image/jpeg\r\n
        line = ifh.readline() # Content-Length:        1985\r\n
        line = ifh.readline() #   (empty line)

        while True:
            line = ifh.readline() 
            if boundary_re.match(line):
                print 'found ending boundary'
                ofh.close()
                return
            else:
                ofh.write(line)
    else:
        print 'could not find a boundary line'

try:
    get_last_10_images()
    save_stream_to_a_file()
    parse_image_lines()
except Exception, e:
    print e
