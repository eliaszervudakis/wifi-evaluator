from collections import OrderedDict
import re

def create_latex_table(capture_id):
    result_file = 'capture/{}/{}_results.txt'.format(capture_id,capture_id)
    table_file = 'capture/{}/{}_table.tex'.format(capture_id,capture_id)

    with open(result_file, 'r+') as result_file, open(table_file, 'w') as table_file:
        content = result_file.read()
        regex_dict = OrderedDict()
        
        regex_dict[r"Channel ([0-9][0-9]): ([\w. ]*)\n\nChannel recommendation: ([0-9, ]*)"] = r"Channel \1 & \2 \\\\ \\hline\nChannel recommendation & \3 \\\\ \\hline\n\\end{tabular}\n\\end{table}\n"
        regex_dict[r"Channel ([0-9][0-9]): ([\w. ]*)"] = r"Channel \1 & \2 \\\\"
        regex_dict[r"[0-9][AB]?\) ([\w, ():]*)"] = r"\\begin{table}[H]\n\\centering\n\\caption{\1}\n\\begin{tabular}{ll}"

        for pattern in regex_dict:
            content = re.sub(pattern, regex_dict[pattern], content)

        table_file.write(content)