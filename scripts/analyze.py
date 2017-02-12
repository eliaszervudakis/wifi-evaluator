import json
import chardet
from collections import defaultdict
import math

## Options / Dictionaries
# 
cck_datarates = ('2', '4', '11', '22')
ofdm_datarates = ('12', '18', '24', '36', '48', '72', '96', '108')

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

# Safe get() method for lists
#
def safe_get(packetdata, key, default):
    l = packetdata.get(key, False)
    try:
        return l[0]
    except IndexError:
        return default
    except TypeError:
        return default

# Filters out non-ascii and control characters
#
def is_ok(s):
    if all(ord(c) < 128 for c in s): # Filter out non-ascii characters
        return all(ord(c) > 32 for c in s) # Filter out control characters
    else:
        return False

# Returns a list of the smallest values in a dict
#
def min_values(d): 
    min_value = min(d.values())
    return [k for k in d if d[k] == min_value]

# Calculates the recommended channels out of a dict
# Returns a pretty printed string
#

def calculate_recommendations(d):
    recommendations = min_values(d)
    result = "\nChannel recommendation: "

    i = 0
    for recommendation in sorted(recommendations):
        if i != len(recommendations)-1:
            result += "{}, ".format(frequency_to_channel_dict[recommendation])
        else:
            result += "{}".format(frequency_to_channel_dict[recommendation])
        i += 1

    return result

def analyze(capture_id,capture_interval):
    analyzing_file =  'capture/{}/{}.json'.format(capture_id,capture_id)
    result_file = 'capture/{}/{}.txt'.format(capture_id,capture_id)

    with open(analyzing_file, 'r') as f_json_analyzing_file, open(result_file, 'w+') as txt_result_file:
        # Set up result collection vars
        #
        frame_len_total = 0
        data_per_sender_dict = defaultdict(int)
        ssid_per_channel_dict = defaultdict(set)

        search_spectrum = [-5,-10,-15,0,5,10,15]

        frequency_list = [2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472]
        ssid_per_channel_dict = {k: set() for k in frequency_list}
        clients_per_channel_dict = {k: set() for k in frequency_list}
        data_per_channel_dict = {k: 0 for k in frequency_list}
        duration_per_channel_dict = {k: 0 for k in frequency_list}
        airtime_per_channel_dict = {k: 0 for k in frequency_list}
        
        # Read json file
        #
        j_json_analyzing_file = json.load(f_json_analyzing_file)
        for packet in j_json_analyzing_file:
            packetdata = packet["_source"]["layers"]

            frame_len = int(packetdata["frame.len"][0])
            frame_number = int(packetdata["frame.number"][0])
            wlan_ta = safe_get(packetdata, "wlan.ta", False)
            wlan_mgt_ssid = safe_get(packetdata, "wlan_mgt.ssid", False)
            radiotap_channel_freq = int(safe_get(packetdata, "radiotap.channel.freq", False))
            wlan_fcs_good = bool(int(safe_get(packetdata, "wlan.fcs.status", False))) # 1==Good, 0==False
            wlan_duration = int(safe_get(packetdata, "wlan.duration", False))

            frame_len_total += frame_len

            if wlan_fcs_good: # Bad packets contain malformed data
                if radiotap_channel_freq:
                    if wlan_mgt_ssid:
                        if is_ok(wlan_mgt_ssid):
                            ssid_per_channel_dict[radiotap_channel_freq].add(wlan_mgt_ssid)
                    if wlan_ta:
                        clients_per_channel_dict[radiotap_channel_freq].add(wlan_ta)

            if wlan_ta:
                data_per_sender_dict[wlan_ta] += frame_len

            if radiotap_channel_freq:
                data_per_channel_dict[radiotap_channel_freq] += frame_len
                duration_per_channel_dict[radiotap_channel_freq] += wlan_duration

            # Caluclate airtime
            #
            time = packetdata["frame.time_relative"][0]
            rate = packetdata["radiotap.datarate"][0]
            size = packetdata["frame.len"][0]
            if rate in cck_datarates:
              airtime_seconds = 192 + float(size) * 16 / float (rate)
            elif rate in ofdm_datarates:
              airtime_seconds = 26 + float(size) * 16 / float (rate)
            else:
              airtime_seconds = 0
            airtime_per_channel_dict[radiotap_channel_freq] += airtime_seconds /1000000

        # Analyze
        #

        #txt_result_file.writelines("Frame len total: {}".format(frame_len_total))
        #txt_result_file.writelines("data_per_sender_dict: {}".format(data_per_sender_dict))
        #txt_result_file.writelines("ssid_per_channel_dict: {}".format(ssid_per_channel_dict))

        # COMPARISION 1A: Number of networks per channel
        #

        txt_result_file.writelines("1A) Networks per channel:\n")
        for channel in sorted(ssid_per_channel_dict):
            active_networks = ssid_per_channel_dict[channel]
            no_of_active_networks = len(ssid_per_channel_dict[channel])
            #txt_result_file.writelines("Channel {}: {} ({})\n".format(frequency_to_channel_dict[channel],no_of_active_networks,active_networks))
            txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_networks))

        txt_result_file.writelines(calculate_recommendations(ssid_per_channel_dict))

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

        txt_result_file.writelines(calculate_recommendations(ssid_per_channel_and_neighbors_dict))
        
        # COMPARISION 2A: Number of clients on the same channel
        # 
        
        txt_result_file.writelines("\n2A) Clients per channel:\n")
        for channel in sorted(clients_per_channel_dict):
            active_clients = clients_per_channel_dict[channel]
            no_of_active_clients = len(clients_per_channel_dict[channel])
            #txt_result_file.writelines("Channel {}: {} ({})\n".format(frequency_to_channel_dict[channel],no_of_active_clients,active_clients))
            txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_clients))
        
        txt_result_file.writelines(calculate_recommendations(clients_per_channel_dict))

        # COMPARISION 2B: Number of clients on the same and neighboring channel
        # 

        txt_result_file.writelines("\n2B) Clients and neigboring clients per channel:\n")
        clients_per_channel_dict_tmp = clients_per_channel_dict.copy()
        clients_per_channel_and_neighbors_dict = {k: 0 for k in frequency_list}
        for channel in sorted(clients_per_channel_dict):
            no_of_active_clients = 0 # len(clients_per_channel_dict[channel])

            # duration_per_channel_dict[channel]
            for i in search_spectrum:
                if channel+i in clients_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                    no_of_active_clients += len(clients_per_channel_dict[channel+i])
                    clients_per_channel_and_neighbors_dict[channel] += len(clients_per_channel_dict[channel+i])

            #txt_result_file.writelines("Channel {}: {} ({})".format(frequency_to_channel_dict[channel],no_of_active_clients,active_clients))
            txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],no_of_active_clients))
        
        txt_result_file.writelines(calculate_recommendations(clients_per_channel_and_neighbors_dict))   
        
        # COMPARISION 3: Utilization per channel (Bytes captured)
        # 
        
        txt_result_file.writelines("\n3) Utilization per channel (Bytes captured)\n")
        for channel in sorted(data_per_channel_dict):
            data = data_per_channel_dict[channel]
            txt_result_file.writelines("Channel {}: {}\n".format(frequency_to_channel_dict[channel],data))
        
        txt_result_file.writelines(calculate_recommendations(data_per_channel_dict))
        
        # COMPARISION 4A: Utilization per channel (Announced duration in seconds)
        # 
        
        txt_result_file.writelines("\n4A) Utilization per channel (Announced duration in seconds)\n")
        for channel in sorted(duration_per_channel_dict):
            duration = duration_per_channel_dict[channel]
            txt_result_file.writelines("Channel {}: {}ms / {}s\n".format(frequency_to_channel_dict[channel],duration,duration/1000000))

        txt_result_file.writelines(calculate_recommendations(duration_per_channel_dict))

        # COMPARISION 4B: Utilization and neighboring utilization per channel (Announced duration in seconds)
        # 
        
        txt_result_file.writelines("\n4B) Utilization and neighboring utilization per channel (Announced duration in seconds)\n")
        duration_per_channel_dict_tmp = duration_per_channel_dict.copy()
        duration_per_channel_and_neighbors_dict = {k: 0 for k in frequency_list}
        for channel in sorted(duration_per_channel_dict):
            duration = 0
            # duration_per_channel_dict[channel]
            for i in search_spectrum:
                if channel+i in duration_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                    duration += duration_per_channel_dict[channel+i]
                    duration_per_channel_and_neighbors_dict[channel] += duration_per_channel_dict[channel+i]
            
            txt_result_file.writelines("Channel {}: {}ms / {}s\n".format(frequency_to_channel_dict[channel],duration,duration/1000000))

        txt_result_file.writelines(calculate_recommendations(duration_per_channel_and_neighbors_dict))

        # COMPARISION 5A: Utilization per channel (Airtsize in seconds)
        # 
      
        txt_result_file.writelines("\n5A) Utilization per channel (Airtime in seconds)\n")
        for channel in sorted(airtime_per_channel_dict):
            airtime_seconds = airtime_per_channel_dict[channel]
            txt_result_file.writelines("Channel {}: {:05.2f}s ({:05.2f}% of {}s interval)\n".format(frequency_to_channel_dict[channel],airtime_seconds,airtime_seconds/capture_interval*100,capture_interval))

        txt_result_file.writelines(calculate_recommendations(airtime_per_channel_dict))

        # COMPARISION 5B: Utilization per channel (Airtsize in seconds)
        # 
        
        txt_result_file.writelines("\n5B) Utilization and neighboring utilization per channel (Airtime in seconds)\n")
        airtime_per_channel_dict_tmp = airtime_per_channel_dict.copy()
        airtime_per_channel_dict_and_neighbors_dict = {k: 0 for k in frequency_list}
        for channel in sorted(airtime_per_channel_dict):
            airtime_seconds = 0
            for i in search_spectrum:
                if channel+i in airtime_per_channel_dict_tmp: # for the lower and upper channels, some spectrum is outside of the dict
                    airtime_seconds += airtime_per_channel_dict[channel+i]
                    airtime_per_channel_dict_and_neighbors_dict[channel] += airtime_per_channel_dict[channel+i]
            
            txt_result_file.writelines("Channel {}: {:05.2f}s ({:05.2f}% of {}s interval)\n".format(frequency_to_channel_dict[channel],airtime_seconds,airtime_seconds/capture_interval*100,capture_interval))

        txt_result_file.writelines(calculate_recommendations(airtime_per_channel_dict_and_neighbors_dict))



