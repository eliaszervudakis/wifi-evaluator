import csv
from collections import defaultdict

def analyze(capture_id):
    print("Analyzing")
    analyzing_file =  'capture/{}/{}.csv'.format(capture_id,capture_id)
    with open(analyzing_file, 'r') as csv_analyzing_file:
        reader = csv.reader(csv_analyzing_file, delimiter=',')

        frame_len_total = 0
        data_per_sender_dict = defaultdict(int)
        # data_per_sender_dict[sender] = 34289
        for row in reader:
            if row[0] == "frame.number":
                continue
            frame_len = int(row[2])
            wlan_sa = row[4]
            frame_len_total += frame_len
            if wlan_sa:
                data_per_sender_dict[wlan_sa] += frame_len

    print("Frame len total: {}".format(frame_len_total))
    print("data_per_sender_dict: {}".format(data_per_sender_dict))