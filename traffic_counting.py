import cv2
import numpy as np
import time
import copy
import os
import glob
import multiprocessing as mpr
from datetime import datetime
import argparse
from kalman_filter import KalmanFilter
from tracker import Tracker

from yolo import YOLO, detect_video


if __name__ == '__main__':

	parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)

	
	parser.add_argument(
        '--image', default=False, action="store_true",
        help='Image detection mode, will ignore all positional arguments'
    )
	parser.add_argument(
        "--input", nargs='?', type=str,required=False,default='./path2your_video',
        help = "Video input path"
    )
	FLAGS = parser.parse_args()
	if FLAGS.image:
		1
	elif "input" in FLAGS:
		hihi = YOLO(**vars(FLAGS))
	else:
		print("Must specify at least video_input_path.  See usage with --help.")
	
	FPS = 60
	'''
		Distance to line in road: ~0.025 miles
	'''
	ROAD_DIST_MILES = 0.001

	'''
		Speed limit of urban freeways in California (50-65 MPH)
	'''
	HIGHWAY_SPEED_LIMIT = 60

	# Initial background subtractor and text font
	fgbg = cv2.createBackgroundSubtractorMOG2()
	

	centers = [] 

	# y-cooridinate for speed detection line
	Y_THRESH = 160
	font = cv2.FONT_HERSHEY_PLAIN
	blob_min_width_far = 50
	blob_min_height_far = 50

	blob_min_width_near = 50
	blob_min_height_near = 50

	frame_start_time = None
	
	# Create object tracker
	tracker = Tracker(80, 3, 2, 1)

	# Capture livestream
	cap = cv2.VideoCapture ('test2.mp4')

	
	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(1,1))
	while True:
		centers = []
		frame_start_time = datetime.utcnow()

		ret, frame = cap.read()
		pts = np.array( [[[0,0],[1280,0],[1280,720],[1080,720],[980,180],[830,180],[0,530]]], dtype=np.int32 )
		cv2.fillPoly( frame, pts, 0 )
		frame2 = frame
		frame,boxes = hihi.detect_image(frame)

		#  Draw line used for speed detection
		cv2.line(frame,(0, Y_THRESH),(640, Y_THRESH),(255,0,0),2)


		for cnt in boxes:
			x, y, w, h = cnt

			if y > Y_THRESH:
				if w >= blob_min_width_near and h >= blob_min_height_near:
					center = np.array ([[x+w/2], [y+h/2]])
					centers.append(np.round(center))

					cv2.rectangle(frame2, (x, y), (x+w, y+h), (0, 255, 0), 2)
			else:
				if w >= blob_min_width_far and h >= blob_min_height_far:
					center = np.array ([[x+w/2], [y+h/2]])
					centers.append(np.round(center))

					cv2.rectangle(frame2, (x, y), (x+w, y+h), (0, 255, 0), 2)

		if centers:
			tracker.update(centers)

			for vehicle in tracker.tracks:
				if len(vehicle.trace) > 1:
					for j in range(len(vehicle.trace)-1):
						x1 = vehicle.trace[j][0][0]
						y1 = vehicle.trace[j][1][0]
						x2 = vehicle.trace[j+1][0][0]
						y2 = vehicle.trace[j+1][1][0]

					try:

						trace_i = len(vehicle.trace) - 1

						trace_x = vehicle.trace[trace_i][0][0]
						trace_y = vehicle.trace[trace_i][1][0]

						if trace_y <= Y_THRESH + 5 and trace_y >= Y_THRESH - 5 and not vehicle.passed:
							cv2.putText(frame, 'I PASSED!', (int(trace_x), int(trace_y)), font, 1, (0, 255, 255), 1, cv2.LINE_AA)
							vehicle.passed = True

							load_lag = (datetime.utcnow() - frame_start_time).total_seconds()

							time_dur = (datetime.utcnow() - vehicle.start_time).total_seconds() - load_lag
							time_dur /= 60
							time_dur /= 60

							
							vehicle.mph = ROAD_DIST_MILES / time_dur

							'''if vehicle.mph > HIGHWAY_SPEED_LIMIT:
								print ('Quá tốc độ!')
								cv2.circle(frame2, (int(trace_x), int(trace_y)), 20, (0, 0, 255), 2)
								cv2.putText(frame2, 'MPH: %s' % int(vehicle.mph), (int(trace_x), int(trace_y)), font, 1, (0, 0, 255), 1, cv2.LINE_AA)
								cv2.imwrite('speeding_%s.png' % vehicle.track_id, orig_frame)'''

					
						if vehicle.passed and vehicle.mph > 10:
							cv2.putText(frame2, '%s km/h' % int(vehicle.mph), (int(trace_x), int(trace_y)), font, 2, (0, 0, 255), 1, cv2.LINE_AA)
					except:
						pass


		# Display all images
		cv2.imshow ('original', frame2)

		# Quit when escape key pressed
		if cv2.waitKey(5) == 27:
			break

		# Sleep to keep video speed consistent
		time.sleep(1.0 / FPS)

	# Clean up
	cap.release()
	cv2.destroyAllWindows()

	# remove all speeding_*.png images created in runtime
	for file in glob.glob('speeding_*.png'):
		os.remove(file)
