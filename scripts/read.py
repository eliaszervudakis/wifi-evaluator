import subprocess
from time import sleep
import re

def read(capture_id):
    # tshark = Wireshark command line tool
    capture_file = r'capture/{}/{}.pcap'.format(capture_id,capture_id)
    analyzing_file =  r'capture/{}/{}.csv'.format(capture_id,capture_id)
    analyzing_file2 =  r'capture/{}/{}_2.csv'.format(capture_id,capture_id)
    
    print("Reading file: {}".format(capture_file))
    fields_list = ['frame.number', 'frame.time', 'frame.len','frame.cap_len', #0-3
    'wlan.sa', 'wlan.da','wlan.ra','wlan.ta','wlan.fcs_bad', # 4-8
    'radiotap.xchannel.channel','radiotap.xchannel.freq','radiotap.channel.freq','wlan_radio.11n.bandwidth', #9-12
    'wlan_radio.data_rate','wlan_mgt.ssid','wlan.duration'] # 13-15
    fields_string = ' -e '.join(fields_list)
    command = "tshark -r {} -T fields -E header=y -E separator=, -E quote=d -e {}  >  {}".format(capture_file,fields_string,analyzing_file)
    subprocess.Popen(command, shell=True)

    sleep(5)

    # Clean up
    # TODO: Fix bug

    with open(analyzing_file, 'r+') as csv_analyzing_file:
        content = csv_analyzing_file.read()

    pattern1 = re.compile(r'"[^"]*[�]+[^"]*"')
    pattern2 = re.compile(r'"""')
    content = pattern1.sub("", content)
    content = pattern1.sub("", content)
    content = pattern2.sub('""', content)

    with open(analyzing_file2, 'w') as csv_analyzing_file:
        csv_analyzing_file.write(content)
