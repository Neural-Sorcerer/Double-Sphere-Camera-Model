import os
import cv2
import copy
import numpy as np

from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
from time import sleep, perf_counter as timer

from dscamera import DSCamera


HD = (1280, 720)
FHD = (1920, 1080)


def run_inference_pipeline(args, freeze=0, resolution=FHD, save_fps=None, fps_limit=None, winname="Inference"):
    # Load Double Sphere Camera Model
    cam = DSCamera(args.json_path)
    
    # Initialize VideoCapture
    cap = cv2.VideoCapture(args.source)

    # Set VideoCapture's properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])        # only for camera
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])       # only for camera
    cap.set(cv2.CAP_PROP_POS_MSEC, 0)                       # only for video file (or)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)                     # only for video file (or)
        
    # Get VideoCapture's properties
    cap_fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))     # only for video file
    
    # Initialize variables
    fps_limit = fps_limit or cap_fps
    save_fps = save_fps or fps_limit
    cap_resolution = (cap_width, cap_height)
    
    # Create a window named
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)

    # Resize the window to specific width and height
    cv2.resizeWindow(winname, width=HD[0]*2, height=HD[1])
    
    # Set the window position
    cv2.moveWindow(winname, x=FHD[0]//2-HD[0]//2, y=FHD[1]//4-HD[1]//4)
    
    # Recording
    if args.save:
        cur_date_time = datetime.now().strftime("%Y.%m.%d.%H-%M-%S")
        cur_date = ".".join(cur_date_time.split(".")[:3])

        original_path = os.path.join(args.output_dir, cur_date, "original", f"{cur_date_time}.mp4")
        modified_path = os.path.join(args.output_dir, cur_date, "modified", f"{cur_date_time}.mp4")
        
        Path(os.path.dirname(original_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(modified_path)).mkdir(parents=True, exist_ok=True)

        fourcc_MJPG = cv2.VideoWriter_fourcc(*'MJPG')   # (.avi) for motion JPEG
        fourcc_XVID = cv2.VideoWriter_fourcc(*'XVID')   # (.avi) for MPEG-4
        fourcc_mp4v = cv2.VideoWriter_fourcc(*'mp4v')   # (.mp4) for MPEG-4
        
        out_org = cv2.VideoWriter(original_path, fourcc_mp4v, save_fps, cap_resolution, isColor=True)
        out_mod = cv2.VideoWriter(modified_path, fourcc_mp4v, save_fps, (cap_width*2, cap_height), isColor=True)

    count = 0
    count_skip = 0
    count_warm_up = 5
    init_time = timer()
    time_limit = timer()
    while (cap.isOpened()) and ((timer() - time_limit) < args.duration):
        count += 1
        start = timer()

        success, original = cap.read()

        if not success:
            break

        if count < count_skip:
            continue
        
        # Copy original frame
        frame = copy.copy(original)

        # Main process
        # =======================================================================================================
        inference_speed_start = timer()
        
        # Image rectification
        pinhole = cam.to_perspective(frame)
        equirectangular = cam.to_equirect(frame)
    
        inference_speed_end = timer()
        # =======================================================================================================

        # Record video
        if args.save:
            out_org.write(original)
            out_mod.write(concatenated_frame)

        # Concatenate frames
        concatenated_frame = np.concatenate((frame, pinhole), axis=1)

        # Show frame
        # cv2.imshow(winname, frame)
        # cv2.imshow("Pinhole", pinhole)
        # cv2.imshow("Equirectangular", equirectangular)
        cv2.imshow(winname, concatenated_frame)
            
        # WaitKey
        if cv2.waitKey(freeze) & 0xFF == ord('q'):
            break

        # Limit the inferece speed by fps_limit
        if fps_limit > 0:
            sleep_time = (1 / fps_limit) - (timer() - init_time)
            if sleep_time > 0:
                sleep(sleep_time)
            init_time = timer()

        # Caluclate inference speed
        fps = round(1 / (timer() - start))
        ms = inference_speed_end - inference_speed_start

        # Start the timer after warming up
        if count-1 == (count_warm_up+count_skip):
            start_avg = timer()
        
        # Show the Inference Speed
        print(f"FPS: {fps}, frameID: {count}")
        print(f"Inference speed FPS: {round(1 / (ms))}")
        print(f"Inference speed: {round(ms, 5)} ms")
        print("="*80)

    print(f"Average FPS: {round(1 / ((timer() - start_avg) / (count-count_warm_up-count_skip)))}")

    # Destroy all the windows
    cap.release()
    if args.save:
        out_org.release()
        out_mod.release()
    cv2.destroyAllWindows()


def main():
    json_path = "./assets/calibration.json"
    video_path = os.path.join('samples', 'F-RGB.mp4')
    # video_path = "/home/max/Downloads/STORAGE/SCMS - Video - Results/test_video_driving/distraction_phone_normal.mp4"
    
    parser = ArgumentParser()
    parser.add_argument('--source', default=video_path, type=str, help='camera/video file path')
    parser.add_argument('--json-path', default=json_path, type=str, help='path to camera calibration parameters')
    parser.add_argument('--duration', default=float('inf'), type=float, help='running time')
    parser.add_argument('--output-dir', default="output", type=str, help='output path')
    parser.add_argument('--save', action="store_true", help='save results')
    args = parser.parse_args()

    if len(args.source) == 1:
        args.source = int(args.source)
    
    run_inference_pipeline(args)


if __name__ == '__main__':
    main()
"""
# Fisheye view
                "intrinsics": {
                    "fx": 485.485,
                    "fy": 485.885,
                    "cx": 949.413,
                    "cy": 523.732,
                    "xi": -0.189386,
                    "alpha": 0.64201
                    }

# Rectangular view
                "intrinsics": {
                    "fx": 606.257,
                    "fy": 546.661,
                    "cx": 944.575,
                    "cy": 525.592,
                    "xi": 2.92628e-10,
                    "alpha": 0.50456
                    }
"""
