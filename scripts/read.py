import subprocess
from time import sleep
import re

def read(capture_id):
    # tshark = Wireshark command line tool
    capture_file = r'capture/{}/{}.pcap'.format(capture_id,capture_id)
    output_file =  r'capture/{}/{}.json'.format(capture_id,capture_id)
    
    print("Reading file: {}".format(capture_file))
    fields_list = ['frame.number', 'frame.time', 'frame.len','frame.cap_len', 'frame.time_relative',
                    'wlan.sa','wlan.ta', 'wlan.da','wlan.ra','wlan.fcs.status', # 'wlan.fcs_bad' 4-8
                    'radiotap.xchannel.channel','radiotap.xchannel.freq','radiotap.channel.freq','wlan_radio.channel','wlan_radio.11n.bandwidth', #9-12
                    'wlan_radio.data_rate','radiotap.datarate','wlan.duration',
                    'wlan_mgt.ssid']
    fields_string = ' -e '.join(fields_list)
    command = "tshark -r {} -T json -E header=y -E separator=, -E quote=d -e {}  >  {}".format(capture_file,fields_string,output_file) #-T  fields
    subprocess.Popen(command, shell=True)