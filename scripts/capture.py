import os
import glob
import signal
import subprocess
import shutil
from time import sleep

def capture(capture_id):
    # Options
    capture_seconds = 60
    capture_interface = "en0"
    channel_list = [1,2,3,4,5,6,7,8,9,10,11,12,13]
    
    capture_folder_tmp = "/private/tmp"
    capture_folder = r'capture/{}'.format(capture_id)

    # Delete old capture files
    for file in glob.glob("{}/airportSniff*.cap".format(capture_folder_tmp)):
        print("Deleted old file: {}\n".format(file))
        os.remove(file)

    # Create new directory for this capture
    print("Current Capture ID: {}\n".format(capture_id))
    if not os.path.exists(capture_folder):
        os.makedirs(capture_folder)

    # Capture traffic for capture_seconds seconds on capture_channel on capture_interface
    for capture_channel in channel_list:
        print("Capturing traffic on channel {}".format(capture_channel))
        command = "airport {} sniff {}".format(capture_interface,capture_channel)
        pro = subprocess.Popen(command, stdout=subprocess.PIPE, 
                               shell=True, preexec_fn=os.setsid) 
        sleep(capture_seconds)
        os.killpg(os.getpgid(pro.pid), signal.SIGINT)

    print("")
    # Copy captured files
    for file in glob.glob("{}/airportSniff*.cap".format(capture_folder_tmp)):
        print("Copied file: {}".format(file))                                                                                                                                      
        shutil.move(file, capture_folder)

    print("Finished capturing traffic\n")

    # Merge captured files
    # mergecap -F pcap -w merged.pcap airportSniffxb4eG5.cap airportSniffG9gS5H.cap
    capture_folder = r'capture/{}'.format(capture_id)
    captured_files_list = list(glob.glob("{}/airportSniff*.cap".format(capture_folder)))
    captured_files_string = ' '.join(captured_files_list)

    capture_file = r'capture/{}/{}.pcap'.format(capture_id,capture_id)

    command = "mergecap -F pcap -w {} {}".format(capture_file,captured_files_string)
    subprocess.Popen(command, shell=True)