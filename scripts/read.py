import subprocess
def read(capture_id):
    # tshark = Wireshark command line tool
    capture_file = r'capture/{}/{}.pcap'.format(capture_id,capture_id)
    analyzing_file =  r'capture/{}/{}.csv'.format(capture_id,capture_id)
    
    print("Reading file: {}".format(capture_file))
    fields_list = ['frame.number', 'frame.time', 'frame.len','frame.cap_len',
    'wlan.sa', 'wlan.da','wlan.ra','wlan.ta','wlan.fcs_bad',
    'radiotap.xchannel.channel','radiotap.xchannel.freq','radiotap.channel.freq','wlan_radio.11n.bandwidth',
    'wlan_radio.data_rate']
    fields_string = ' -e '.join(fields_list)
    command = "tshark -r {} -T fields -E header=y -E separator=, -E quote=d -e {}  >  {}".format(capture_file,fields_string,analyzing_file)
    subprocess.Popen(command, shell=True)