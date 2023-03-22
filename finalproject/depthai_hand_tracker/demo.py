#!/usr/bin/env python3


from HandTrackerRenderer import HandTrackerRenderer
import argparse
import time
import donkeycar as dk

class VESC:
    ''' 
    VESC Motor controler using pyvesc
    This is used for most electric scateboards.
    
    inputs: serial_port---- port used communicate with vesc. for linux should be something like /dev/ttyACM1
    has_sensor=False------- default value from pyvesc
    start_heartbeat=True----default value from pyvesc (I believe this sets up a heartbeat and kills speed if lost)
    baudrate=115200--------- baudrate used for communication with VESC
    timeout=0.05-------------time it will try before giving up on establishing connection
    
    percent=.2--------------max percentage of the dutycycle that the motor will be set to
    outputs: none
    
    uses the pyvesc library to open communication with the VESC and sets the servo to the angle (0-1) and the duty_cycle(speed of the car) to the throttle (mapped so that percentage will be max/min speed)
    
    Note that this depends on pyvesc, but using pip install pyvesc will create a pyvesc file that
    can only set the speed, but not set the servo angle. 
    
    Instead please use:
    pip install git+https://github.com/LiamBindle/PyVESC.git@master
    to install the pyvesc library
    '''
    def __init__(self, serial_port, percent=.2, has_sensor=False, start_heartbeat=True, baudrate=115200, timeout=0.05, steering_scale = 1.0, steering_offset = 0.0 ):
        
        try:
            import pyvesc
        except Exception as err:
            print("\n\n\n\n", err, "\n")
            print("please use the following command to import pyvesc so that you can also set")
            print("the servo position:")
            print("pip install git+https://github.com/LiamBindle/PyVESC.git@master")
            print("\n\n\n")
            time.sleep(1)
            raise
        
        assert percent <= 1 and percent >= -1,'\n\nOnly percentages are allowed for MAX_VESC_SPEED (we recommend a value of about .2) (negative values flip direction of motor)'
        self.steering_scale = steering_scale
        self.steering_offset = steering_offset
        self.percent = percent
        
        try:
            self.v = pyvesc.VESC(serial_port, has_sensor, start_heartbeat, baudrate, timeout)
        except Exception as err:
            print("\n\n\n\n", err)
            print("\n\nto fix permission denied errors, try running the following command:")
            print("sudo chmod a+rw {}".format(serial_port), "\n\n\n\n")
            time.sleep(1)
            raise
        
    def run(self, angle, throttle):
        self.v.set_servo((angle * self.steering_scale) + self.steering_offset)
        self.v.set_duty_cycle(throttle*self.percent)

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--edge', action="store_true",
                    help="Use Edge mode (postprocessing runs on the device)")
parser_tracker = parser.add_argument_group("Tracker arguments")
parser_tracker.add_argument('-i', '--input', type=str, 
                    help="Path to video or image file to use as input (if not specified, use OAK color camera)")
parser_tracker.add_argument("--pd_model", type=str,
                    help="Path to a blob file for palm detection model")
parser_tracker.add_argument('--no_lm', action="store_true", 
                    help="Only the palm detection model is run (no hand landmark model)")
parser_tracker.add_argument("--lm_model", type=str,
                    help="Landmark model 'full', 'lite', 'sparse' or path to a blob file")
parser_tracker.add_argument('--use_world_landmarks', action="store_true", 
                    help="Fetch landmark 3D coordinates in meter")
parser_tracker.add_argument('-s', '--solo', action="store_true", 
                    help="Solo mode: detect one hand max. If not used, detect 2 hands max (Duo mode)")                    
parser_tracker.add_argument('-xyz', "--xyz", action="store_true", 
                    help="Enable spatial location measure of palm centers")
parser_tracker.add_argument('-g', '--gesture', action="store_true", 
                    help="Enable gesture recognition")
parser_tracker.add_argument('-c', '--crop', action="store_true", 
                    help="Center crop frames to a square shape")
parser_tracker.add_argument('-f', '--internal_fps', type=int, 
                    help="Fps of internal color camera. Too high value lower NN fps (default= depends on the model)")                    
parser_tracker.add_argument("-r", "--resolution", choices=['full', 'ultra'], default='full',
                    help="Sensor resolution: 'full' (1920x1080) or 'ultra' (3840x2160) (default=%(default)s)")
parser_tracker.add_argument('--internal_frame_height', type=int,                                                                                 
                    help="Internal color camera frame height in pixels")   
parser_tracker.add_argument("-lh", "--use_last_handedness", action="store_true",
                    help="Use last inferred handedness. Otherwise use handedness average (more robust)")                            
parser_tracker.add_argument('--single_hand_tolerance_thresh', type=int, default=10,
                    help="(Duo mode only) Number of frames after only one hand is detected before calling palm detection (default=%(default)s)")
parser_tracker.add_argument('--dont_force_same_image', action="store_true",
                    help="(Edge Duo mode only) Don't force the use the same image when inferring the landmarks of the 2 hands (slower but skeleton less shifted)")
parser_tracker.add_argument('-lmt', '--lm_nb_threads', type=int, choices=[1,2], default=2, 
                    help="Number of the landmark model inference threads (default=%(default)i)")  
parser_tracker.add_argument('-t', '--trace', type=int, nargs="?", const=1, default=0, 
                    help="Print some debug infos. The type of info depends on the optional argument.")                
parser_renderer = parser.add_argument_group("Renderer arguments")
parser_renderer.add_argument('-o', '--output', 
                    help="Path to output video file")
args = parser.parse_args()
dargs = vars(args)
tracker_args = {a:dargs[a] for a in ['pd_model', 'lm_model', 'internal_fps', 'internal_frame_height'] if dargs[a] is not None}

if args.edge:
    from HandTrackerEdge import HandTracker
    tracker_args['use_same_image'] = not args.dont_force_same_image
else:
    from HandTracker import HandTracker


tracker = HandTracker(
        input_src=args.input, 
        use_lm= not args.no_lm, 
        use_world_landmarks=args.use_world_landmarks,
        use_gesture=args.gesture,
        xyz=args.xyz,
        solo=args.solo,
        crop=args.crop,
        resolution=args.resolution,
        stats=True,
        trace=args.trace,
        use_handedness_average=not args.use_last_handedness,
        single_hand_tolerance_thresh=args.single_hand_tolerance_thresh,
        lm_nb_threads=args.lm_nb_threads,
        **tracker_args
        )

renderer = HandTrackerRenderer(
        tracker=tracker,
        output=args.output)

cfg = dk.load_config(config_path='config.py')

vesc = VESC(cfg.VESC_SERIAL_PORT,
                      cfg.VESC_MAX_SPEED_PERCENT,
                      cfg.VESC_HAS_SENSOR,
                      cfg.VESC_START_HEARTBEAT,
                      cfg.VESC_BAUDRATE, 
                      cfg.VESC_TIMEOUT,
                      cfg.VESC_STEERING_SCALE,
                      cfg.VESC_STEERING_OFFSET
                    )

while True:
    # Run hand tracker on next frame
    # 'bag' contains some information related to the frame 
    # and not related to a particular hand like body keypoints in Body Pre Focusing mode
    # Currently 'bag' contains meaningful information only when Body Pre Focusing is used
    frame, hands, bag = tracker.next_frame()
    if frame is None: break
    # Draw hands
    frame = renderer.draw(frame, hands, bag)
    key = renderer.waitKey(delay=1)
    if key == 27 or key == ord('q'):
        break
    if len(hands) > 0:
        if hands[0].gesture == "GO":
            VESC.run(vesc, 0, 0.3)
        elif hands[0].gesture == "STOP":
            VESC.run(vesc, 0, 0)
        elif hands[0].gesture == "LEFT":
            VESC.run(vesc, -1, 0.3)
        elif hands[0].gesture == "RIGHT":
            VESC.run(vesc, 1, 0.3)
        print(str(hands[0].gesture))
renderer.exit()
tracker.exit()
