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

# Neighboring networks are networks within +-10MhZ => The 3 channels before and after
search_spectrum = [-5,-10,-15,0,5,10,15]

# Frequencys for channels 1-13
frequency_list = [2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472]

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

# Creates the recommended channels out of a dict
# Returns a pretty printed string
#

def create_channel_recommendations(d):
    recommendations = min_values(d)
    result = "\nChannel recommendation: "

    i = 0
    for recommendation in sorted(recommendations):
        if i != len(recommendations)-1:
            result += "{}, ".format(frequency_to_channel_dict[recommendation])
        else:
            result += "{}".format(frequency_to_channel_dict[recommendation])
        i += 1

    result += "\n"
    return result

# Creates the channel overview
#
def create_channel_overview(d,debug=False,islist=True,padding="",unit=""):
    result = ""

    for frequency in sorted(d):
        value = d[frequency]
        if islist:
            value_len = len(d[frequency])
        else:
            value_len = d[frequency]

        if debug:
            result += "Channel {}: {var:{pad}} {} ({})\n".format(frequency_to_channel_dict[frequency],unit,value,var=value_len,pad=padding)
        else:
            result += "Channel {}: {var:{pad}} {}\n".format(frequency_to_channel_dict[frequency],unit,var=value_len,pad=padding)

    result += create_channel_recommendations(d)
    return result

# Creates the channel overview with neighboring networks
# Neighboring networks are networks within +-10MhZ => The 3 channels before and after
#
def create_channel_overview_with_neighboring(d,debug=False,islist=True,padding="",unit=""):
    result = ""
    tmp = d.copy()
    d_plus = {k: 0 for k in frequency_list}

    for frequency in sorted(d):
        value_len = 0

        for offset in search_spectrum:
            if frequency+offset in tmp: # for the lower and upper channels, some spectrum is outside of the dict
                if islist:
                    value_len += len(d[frequency+offset])
                    d_plus[frequency] += len(tmp[frequency+offset])
                else:
                    value_len += d[frequency+offset]
                    d_plus[frequency] += tmp[frequency+offset]

        value = d_plus[frequency]

        if debug:
            result += "Channel {}: {var:{pad}} {} ({})\n".format(frequency_to_channel_dict[frequency],value,unit,var=value_len,pad=padding)
        else:
            result += "Channel {}: {var:{pad}} {}\n".format(frequency_to_channel_dict[frequency],unit,var=value_len,pad=padding)


    result += create_channel_recommendations(d_plus)
    return result

# Main method
#

def analyze(capture_id,capture_interval):
    analyzing_file =  'capture/{}/{}.json'.format(capture_id,capture_id)
    result_file = 'capture/{}/{}_results.txt'.format(capture_id,capture_id)

    with open(analyzing_file, 'r') as f_json_analyzing_file, open(result_file, 'w+') as txt_result_file:
        # Set up result collection vars
        #
        data_per_sender_dict = defaultdict(int)
        ssid_per_channel_dict = defaultdict(set)
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
            wlan_fcs_good = bool(int(safe_get(packetdata, "wlan.fcs.status", False))) # 1==Good/True, 0==Bad/False
            wlan_duration = int(safe_get(packetdata, "wlan.duration", False))

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
                data_per_channel_dict[radiotap_channel_freq] += frame_len/1000000
                duration_per_channel_dict[radiotap_channel_freq] += wlan_duration/1000000

            # Caluclate airtime out of framelen and datarate
            # Based on: 
            # http://wiki.laptop.org/go/Wireless_airtime_analysis
            # 2007 One Laptop Per Child (OLPC) Wiki
            # Ricardo Carrano <carrano at laptop.org> and Frederick Grose <fgros at sugarlabs.org>
            # 
            datarate = packetdata["radiotap.datarate"][0]
            if datarate in cck_datarates:
              airtime = 192 + frame_len * 16 / float (datarate)
            elif datarate in ofdm_datarates:
              airtime = 26 + frame_len * 16 / float (datarate)
            else:
              airtime = 0
            airtime_per_channel_dict[radiotap_channel_freq] += airtime /1000000

        # Analyze
        #

        # COMPARISION 1A: Number of networks per channel
        #
        txt_result_file.writelines("1A) Networks per channel:\n")
        txt_result_file.writelines(create_channel_overview(ssid_per_channel_dict))

        # COMPARISION 1B: Number of networks and neighboring networks per channel
        #
        txt_result_file.writelines("\n1B) Networks and neighboring networks per channel:\n")
        txt_result_file.writelines(create_channel_overview_with_neighboring(ssid_per_channel_dict))

        # COMPARISION 2A: Number of clients on the same channel
        #       
        txt_result_file.writelines("\n2A) Clients per channel:\n")
        txt_result_file.writelines(create_channel_overview(clients_per_channel_dict))

        # COMPARISION 2B: Number of clients on the same and neighboring channel
        # 
        txt_result_file.writelines("\n2B) Clients and neigboring clients per channel:\n")
        txt_result_file.writelines(create_channel_overview_with_neighboring(clients_per_channel_dict))

        # COMPARISION 3: Utilization per channel (Bytes captured)
        #    
        txt_result_file.writelines("\n3) Utilization per channel (Data in Megabyte (MB))\n")
        txt_result_file.writelines(create_channel_overview(data_per_channel_dict,islist=False,padding="05.2f",unit="MB"))

        # COMPARISION 4A: Utilization per channel (Announced duration in seconds)
        # 
        txt_result_file.writelines("\n4A) Utilization per channel (Announced duration in seconds)\n")
        txt_result_file.writelines(create_channel_overview(duration_per_channel_dict,islist=False,padding="05.2f",unit="s"))

        # COMPARISION 4B: Utilization and neighboring utilization per channel (Announced duration in seconds)
        # 
        txt_result_file.writelines("\n4B) Utilization and neighboring utilization per channel (Announced duration in seconds)\n")
        txt_result_file.writelines(create_channel_overview_with_neighboring(duration_per_channel_dict,islist=False,padding="05.2f",unit="s"))

        # COMPARISION 5A: Utilization per channel (Airtsize in seconds)
        # 
        txt_result_file.writelines("\n5A) Utilization per channel (Airtime in seconds, capture interval: {}s)\n".format(capture_interval))
        txt_result_file.writelines(create_channel_overview(airtime_per_channel_dict,islist=False,padding="05.2f",unit="s"))
        # % of interval: airtime/capture_interval*100

        # COMPARISION 5B: Utilization per channel (Airtsize in seconds)
        # 
        txt_result_file.writelines("\n5B) Utilization and neighboring utilization per channel (Airtime in seconds, capture interval: {}s)\n".format(capture_interval))
        txt_result_file.writelines(create_channel_overview_with_neighboring(airtime_per_channel_dict,islist=False,padding="05.2f",unit="s"))