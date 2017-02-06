import csv
from collections import defaultdict

frequency_to_channel_dict = {
    2412: '01',
    2417: '02',
    2422: '03',
    2427: '04',
    2432: '05',
    2437: '06',
    2442: '07',
    2447: '08',
    2452: '09',
    2457: '10',
    2462: '11',
    2467: '12',
    2472: '13'
}

def analyze(capture_id):
    txt_result_file = open('capture/{}/{}.txt'.format(capture_id,capture_id), 'w+')
    txt_result_file.writelines("Analyzing\n")
    analyzing_file =  'capture/{}/{}.csv'.format(capture_id,capture_id)

    with open(analyzing_file, 'r') as csv_analyzing_file:
        reader = csv.reader(csv_analyzing_file, delimiter=',')

        frame_len_total = 0
        data_per_sender_dict = defaultdict(int) # data_per_sender_dict[sender] = 34289
        ssid_per_channel_dict = defaultdict(set)
        search_spectrum = [-5,-10,-15,0,5,10,15]

        frequency_list = [2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472]
        ssid_per_channel_dict = {k: set() for k in frequency_list}
        clients_per_channel_dict = {k: set() for k in frequency_list}
        data_per_channel_dict = {k: 0 for k in frequency_list}
        duration_per_channel_dict = {k: 0 for k in frequency_list}
    
        for row in reader:
            if row[0] == "frame.number":
                continue
            #txt_result_file.writelines(row)
            frame_len = int(row[2])
            wlan_sa = row[4]
            wlan_mgt_ssid = row[14]
            radiotap_xchannel_channel = row[9]
            radiotap_channel_freq = int(row[11])
            wlan_fcs_bad = row[8]
            frame_len_total += frame_len
            wlan_ta = row[7] # transmitter

            if len(row) < 16:
                #txt_result_file.writelines("len(row{})<16: {}".format(row[0],len(row)))
                wlan_duration = 0
            elif row[15] == '':
                wlan_duration = 0
                #txt_result_file.writelines("empty string")
            else:
                print("frame no. {}".format(row[0]))
                wlan_duration = int(row[15])

            #txt_result_file.writelines("wlan duration: {}".format(wlan_duration))
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
                duration_per_channel_dict[radiotap_channel_freq] += wlan_duration

    #txt_result_file.writelines("Frame len total: {}".format(frame_len_total))
    #txt_result_file.writelines("data_per_sender_dict: {}".format(data_per_sender_dict))
    #txt_result_file.writelines("ssid_per_channel_dict: {}".format(ssid_per_channel_dict))

    # COMPARISION 1A: Number of networks per channel
    #

    txt_result_file.writelines("1A) Networks per channel:\n")
    for channel in sorted(ssid_per_channel_dict):
        active_networks = ssid_per_channel_dict[channel]
        no_of_active_networks = len(ssid_per_channel_dict[channel])
        #txt_result_file.writelines("Channel {}: {} ({})".format(frequency_to_channel_dict[channel],no_of_active_networks,active_networks))
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_networks))

    recommendation = min(ssid_per_channel_dict, key=ssid_per_channel_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))

    # COMPARISION 1B: Number of networks and neighboring networks per channel
    # Neighboring networks are networks within +-10MhZ => The 3 before and after
    #
    # 
    # We check the influence of the neighboring networks on the channels. 
    # How much impact do they have on the channel they’re using and on neighbouring channels.
    # 
    # http://www.metageek.com/training/resources/adjacent-channel-congestion.html

    txt_result_file.writelines("\n1B) Networks and neighboring networks per channel:\n")
    ssid_per_channel_dict_tmp = ssid_per_channel_dict.copy()
    ssid_per_channel_and_neighbors_dict = {k: 0 for k in frequency_list}
    for channel in sorted(ssid_per_channel_dict):
        no_of_active_networks = 0

        for i in search_spectrum:
            if channel+i in ssid_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                no_of_active_networks += len(ssid_per_channel_dict_tmp[channel+i])
                ssid_per_channel_and_neighbors_dict[channel] += len(ssid_per_channel_dict_tmp[channel+i])

        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_networks))

    recommendation = min(ssid_per_channel_and_neighbors_dict, key=ssid_per_channel_and_neighbors_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))
    
    # COMPARISION 3A: Number of clients on the same channel
    # 
    
    txt_result_file.writelines("\n2A) Clients per channel:\n")
    for channel in sorted(clients_per_channel_dict):
        active_clients = clients_per_channel_dict[channel]
        no_of_active_clients = len(clients_per_channel_dict[channel])
        #txt_result_file.writelines("Channel {}: {} ({})".format(frequency_to_channel_dict[channel],no_of_active_clients,active_clients))
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_clients))
    
    recommendation = min(clients_per_channel_dict, key=clients_per_channel_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))

    # COMPARISION 3B: Number of clients on the same and neighboring channel
    # 

    txt_result_file.writelines("\n2B) Clients and neigboring clients per channel:\n")
    clients_per_channel_dict_tmp = clients_per_channel_dict.copy()
    clients_per_channel_and_neighbors_dict = {k: 0 for k in frequency_list}
    for channel in sorted(clients_per_channel_dict):
        no_of_active_clients = 0 # len(clients_per_channel_dict[channel])

        # duration_per_channel_dict[channel]
        for i in search_spectrum:
            if channel+i in clients_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                #txt_result_file.writelines("Channel X+i: {} - Duration: {}".format(channel,channel+i,))
                no_of_active_clients += len(clients_per_channel_dict[channel+i])
                clients_per_channel_and_neighbors_dict[channel] += len(clients_per_channel_dict[channel+i])

        #txt_result_file.writelines("Channel {}: {} ({})".format(frequency_to_channel_dict[channel],no_of_active_clients,active_clients))
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_clients))
    
    recommendation = min(clients_per_channel_and_neighbors_dict, key=clients_per_channel_and_neighbors_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))    
    
    # COMPARISION 4: 
    # 
    
    txt_result_file.writelines("\n3) Utilization per channel (Bytes captured)\n")
    for channel in sorted(data_per_channel_dict):
        data = data_per_channel_dict[channel]
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],data))
    
    recommendation = min(data_per_channel_dict, key=data_per_channel_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))
    
    # COMPARISION 5A: Actual utilization per channel
    # 
    
    txt_result_file.writelines("\n4A) Utilization per channel (Airtime in seconds)\n")
    for channel in sorted(duration_per_channel_dict):
        duration = duration_per_channel_dict[channel]/1000000
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],duration))

    recommendation = min(duration_per_channel_dict, key=duration_per_channel_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))

    # COMPARISION 5B: 
    # 
    
    txt_result_file.writelines("\n4B) Utilization and neighboring utilization per channel (Airtime in seconds)\n")
    #recommendation = min(duration_per_channel_dict, key=duration_per_channel_dict.get)
    #txt_result_file.writelines("Channel recommendation: {}".format(frequency_to_channel_dict[recommendation]))

    duration_per_channel_dict_tmp = duration_per_channel_dict.copy()
    duration_per_channel_and_neighbors_dict = {k: 0 for k in frequency_list}
    for channel in sorted(duration_per_channel_dict):
        duration = 0
        # duration_per_channel_dict[channel]
        for i in search_spectrum:
            if channel+i in duration_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                #txt_result_file.writelines("Channel X+i: {} - Duration: {}".format(channel,channel+i,))
                duration += duration_per_channel_dict[channel+i]
                duration_per_channel_and_neighbors_dict[channel] += duration_per_channel_dict[channel+i]
        
        txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],duration/1000000))

    recommendation = min(duration_per_channel_and_neighbors_dict, key=duration_per_channel_and_neighbors_dict.get)
    txt_result_file.writelines("Channel recommendation: {}\n".format(frequency_to_channel_dict[recommendation]))