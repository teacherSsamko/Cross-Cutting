#%%
# USAGE
# python video_facial_landmarks.py --shape-predictor shape_predictor_68_face_landmarks.dat
# python video_facial_landmarks.py --shape-predictor shape_predictor_68_face_landmarks.dat --picamera 1

# 전체 참고 
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

# import the necessary packages
from imutils.video import VideoStream
from moviepy.editor import VideoFileClip
from imutils import face_utils
import datetime
import argparse
import imutils
import time
import dlib
import cv2
import math
import numpy as np

# Frame 수 줄이면 시간 줄일 수 있음
# 1 frame으로 총 작업하는데 2688.1366200447083 / 4 frame  576.5337190628052
skip_frame_rate = 2
MINMAX_FRAMES = 3 # 주변 frame 중에서 가장 큰 값의 min을 얻어야 함
print('landmark hypeparmeter')
print(skip_frame_rate, MINMAX_FRAMES)

def extract_landmark(reference_clip, compare_clip):
	print("[INFO] loading facial landmark predictor...")
	# 얼굴 자체를 인식하는 기능
	detector = dlib.get_frontal_face_detector()
	# face 안에 얼굴 인식하는 기능
	predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

	# 비디오 출력 : https://076923.github.io/posts/Python-opencv-4/
	# https://docs.opencv.org/master/dd/d43/tutorial_py_video_display.html
	clips =[reference_clip,compare_clip]

	clips_frame_info = []
	for clip in clips:
		i=0
		every_frame_info= []
		# loop over the frames from the video stream
		while True:
			# grab the frame from the threaded video stream, resize it to
			# have a maximum width of 400 pixels, and convert it to
			# ret, frame = capture.read() # frame = numpy array임
			frame = clip.get_frame(i*1.0/clip.fps)
			i+=skip_frame_rate # 1초에 60 fps가 있으므로 몇개는 skip해도 될거 같음!
			if (i*1.0/clip.fps)> clip.duration:
				break
			
			# width 높이면 더 판별 잘되지만, computational power 높음
			# The benefit of increasing the resolution of the input image prior to face detection is that it may allow us to detect more faces in the imag
			# !!! 아니면 너무 느려지면 640으로 낮춰서 해도 괜찮을듯(1280은 너무 세세한거까지 잡음)
			frame = imutils.resize(frame, width=640) ### !!!! 여기 width 계산도 중요하다!(실제 좌표로 옮겨야 하니까) 
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			# detect faces in the grayscale frame
			# 얼굴 자체의 위치를 찾음
			rects = detector(gray, 0)

			if len(rects)>0:
				# 얼굴 개수만큼 loop
				max_width = 0
				max_rect = None
				# 얼굴 박스 제일 큰거 하나로
				for rect in rects:
					if int(rects[0].width()) > max_width:
						max_rect = rect
				# determine the facial landmarks for the face region, then
				# convert the facial landmark (x, y)-coordinates to a NumPy array
				shape = predictor(gray, max_rect)
				shape = face_utils.shape_to_np(shape)
				every_frame_info.append(shape)
			else:
				every_frame_info.append([])
			
		clips_frame_info.append(np.array(every_frame_info))

	cv2.destroyAllWindows()

	return clips_frame_info

def calculate_distance(reference_clip, compare_clip):
	time.sleep(2.0)
	clips_frame_info = extract_landmark(reference_clip, compare_clip) # 모든 프레임마다 길이 계산해줌
	clips =[reference_clip,compare_clip]

	min_size = min(len(clips_frame_info[0]),len(clips_frame_info[1]))
	dist_arr = []
	# Caculate distance by frame
	for i in range(min_size-1):
		if len(clips_frame_info[0][i])>0 and len(clips_frame_info[1][i+1])>0: # 얼굴 둘다 있으면
			# 두 영상에서 눈의 거리(왼쪽 눈 끼리, 오른쪽 눈 끼리)
			l = 36 # 왼쪽 눈 왼쪽 끝
			r = 45 # 오른쪽 눈3 오른쪽 끝
			# 계산할 때 지금 영상은 i초, 다음 영상은 i+1초로 계산하자.
			left_eye = ((clips_frame_info[0][i][l][0] - clips_frame_info[1][i+1][l][0])**2 + (clips_frame_info[0][i][l][1] - clips_frame_info[1][i+1][l][1])**2)**0.5
			right_eye = ((clips_frame_info[0][i][r][0] - clips_frame_info[1][i+1][r][0])**2 + (clips_frame_info[0][i][r][1] - clips_frame_info[1][i+1][r][1])**2)**0.5

			total_diff = left_eye + right_eye
			dist_arr.append(total_diff)
		else:
			dist_arr.append(None)
	
	min_diff = np.float('Inf')
	min_idx = 0
	refer_length = 0
	refer_degree = 0
	compare_length = 0
	compare_degree = 0
	refer_point = []
	compare_point = []
	max_dist = []
	for i in range(min_size - (MINMAX_FRAMES - 1)): # 해당 frame "이전과 이후"에 frame들 확인
		start_minmax_idx = 0 if (i - MINMAX_FRAMES)<0 else i - MINMAX_FRAMES
		if (None in dist_arr[start_minmax_idx :i + MINMAX_FRAMES]):
			max_dist.append(None)
		else:
			tmp_max = np.max(dist_arr[start_minmax_idx:i + MINMAX_FRAMES])
			max_dist.append(tmp_max) # 해당 frame의 가장 최대값
			if min_diff > tmp_max:
				min_diff = tmp_max
				min_idx = i
				#http://www.gisdeveloper.co.kr/?p=1r5
				refer_gradient = (clips_frame_info[0][i][l][1]-clips_frame_info[0][i][r][1]) / (clips_frame_info[0][i][l][0]-clips_frame_info[0][i][r][0])
				refer_degree = math.degrees(math.atan(refer_gradient)) # radian -> degree
				compare_gradient = (clips_frame_info[1][i+1][l][1]-clips_frame_info[1][i+1][r][1]) / (clips_frame_info[1][i+1][l][0]-clips_frame_info[1][i+1][r][0])
				compare_degree = math.degrees(math.atan(compare_gradient)) # radian -> degree
				# 첫번째 영상에서 눈길이
				refer_length = ((clips_frame_info[0][i][l][0] - clips_frame_info[0][i][r][0])**2 + (clips_frame_info[0][i][l][1] - clips_frame_info[0][i][r][1])**2)**0.5
				# 두번째 영상에서 눈길이
				compare_length = ((clips_frame_info[1][i+1][l][0] - clips_frame_info[1][i+1][r][0])**2 + (clips_frame_info[1][i+1][l][1] - clips_frame_info[1][i+1][r][1])**2)**0.5
				# 640 width 로 확인했으면 두배
				refer_point = [(clips_frame_info[0][i][l][0]*2,clips_frame_info[0][i][l][1]*2),
								(clips_frame_info[0][i][r][0]*2,clips_frame_info[0][i][r][1]*2)]
				compare_point =[(clips_frame_info[1][i+1][l][0]*2,clips_frame_info[1][i+1][l][1]*2),
								(clips_frame_info[1][i+1][r][0]*2,clips_frame_info[1][i+1][r][1]*2)]
			
	# 640 width 로 확인했으면 두배
	min_diff = min_diff * 2
	additional_info = {
		"refer_length" : refer_length*2, "refer_degree" : refer_degree, 
		"compare_length" : compare_length*2, "compare_degree" : compare_degree,
		"refer_point" : refer_point, "compare_point" : compare_point 
	} # 거리와 해당 초 위치를 계산해준다!

	return min_diff, (min_idx*skip_frame_rate)/clips[0].fps, additional_info
