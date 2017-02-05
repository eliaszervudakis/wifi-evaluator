import csv
from collections import defaultdict



def analyze(capture_id):
    print("Analyzing")
    analyzing_file =  'capture/{}/{}.csv'.format(capture_id,capture_id)
    with open(analyzing_file, 'r') as csv_analyzing_file:
        reader = csv.reader(csv_analyzing_file, delimiter=',')

        frame_len_total = 0
        data_per_sender_dict = defaultdict(int) # data_per_sender_dict[sender] = 34289
        ssid_per_channel_dict = defaultdict(set)

        frequency_list = [2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472]
        ssid_per_channel_dict = {k: set() for k in frequency_list}
        clients_per_channel_dict = {k: set() for k in frequency_list}
        data_per_channel_dict = {k: 0 for k in frequency_list}
    
        for row in reader:
            if row[0] == "frame.number":
                continue
            #print(row)
            frame_len = int(row[2])
            wlan_sa = row[4]
            wlan_mgt_ssid = row[14]
            radiotap_xchannel_channel = row[9]
            radiotap_channel_freq = int(row[11])
            wlan_fcs_bad = row[8]
            frame_len_total += frame_len
            wlan_ta = row[7] # transmitter

            if wlan_fcs_bad == "0": # Bad packets contain malformed data
                if radiotap_channel_freq:
                    if wlan_mgt_ssid:
                        ssid_per_channel_dict[radiotap_channel_freq].add(wlan_mgt_ssid)
                    if wlan_ta:
                        clients_per_channel_dict[radiotap_channel_freq].add(wlan_ta)

            if wlan_ta:
                data_per_sender_dict[wlan_ta] += frame_len

            if radiotap_channel_freq:
                data_per_channel_dict[radiotap_channel_freq] += frame_len



    print("Frame len total: {}".format(frame_len_total))
    #print("data_per_sender_dict: {}".format(data_per_sender_dict))
    #print("ssid_per_channel_dict: {}".format(ssid_per_channel_dict))

    # COMPARISION 1: Number of networks per channel
    print("1) Active Networks per Channel:")
    for channel in sorted(ssid_per_channel_dict):
        active_networks = ssid_per_channel_dict[channel]
        no_of_active_networks = len(ssid_per_channel_dict[channel])
        print("Frequency {}: {} ({})".format(channel,no_of_active_networks,active_networks))

    # COMPARISION 2: Number of networks and neighboring networks per channel
    # Neighboring networks are networks within +-10MhZ => The 3 before and after
    #
    # 
    # We check the influence of the neighboring networks on the channels. 
    # How much impact do they have on the channel they’re using and on neighbouring channels.
    # 
    # http://www.metageek.com/training/resources/adjacent-channel-congestion.html

    print("2) Active networks and neighboring networks per channel:")
    ssid_per_channel_dict_tmp = ssid_per_channel_dict.copy()
    for channel in sorted(ssid_per_channel_dict):
        search_spectrum = [-5,-10,-15,0,5,10,15]
        no_of_active_networks = 0

        for i in search_spectrum:
            if channel+i in ssid_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                no_of_active_networks += len(ssid_per_channel_dict_tmp[channel+i])

        print("Frequency {}: {}".format(channel,no_of_active_networks))

    # COMPARISION 3: Number of clients on the same channel
    # 
    print("3) Number of clients on the same channel:")
    for channel in sorted(clients_per_channel_dict):
        active_clients = clients_per_channel_dict[channel]
        no_of_active_clients = len(clients_per_channel_dict[channel])
        print("Frequency {}: {} ({})".format(channel,no_of_active_clients,active_clients))
    # COMPARISION 4: 
    # 
    print("4) Actual utilization per channel (Bytes captured)")
    for channel in sorted(data_per_channel_dict):
        data = data_per_channel_dict[channel]
        print("Frequency {}: {}".format(channel,data))
    # COMPARISION 5: 
    # 
    print("5) Actual utilization per channel (Airtime) TODO")


