import os
from datetime import datetime


class Logger:
    def __init__(self, debug=False):
        self.log_folder_path = os.path.join(os.getcwd(), "logs")
        self.curr_log_path = os.path.join(self.log_folder_path, datetime.now().strftime("%Y%m%d%H%M%S.log"))
        self.logs = []
        self.debug = debug
        self.next_line = True

    def log_newline(self, message, debug=False, end='\n\r', other_tag=''):
        if not self.next_line:
            print("", end='\n\r')
            self.next_line = True
        self.log(message, debug, end, other_tag)

    def log(self, message, debug=False, end='\n\r', other_tag=''):
        if debug and not self.debug:
            return
        if not self.next_line:
            log = message
            self.logs[len(self.logs) - 1] = self.logs[len(self.logs) - 1] + log
        else:
            now = datetime.now()
            log = now.strftime("[%H:%M:%S]") + ("[DEBUG]" if debug else "") + other_tag + " " + message
            self.logs.append(log)
        print(log, end=end)
        self.next_line = end == '\n\r'

    def error(self, message):
        self.log("[ERROR] " + message)
        raise Exception(message)

    def write_log(self, max_logs):
        if not os.path.exists(self.log_folder_path):
            os.makedirs(self.log_folder_path)
        # Write logs
        with open(self.curr_log_path, 'w', encoding='UTF8') as f:
            f.write("\n".join(self.logs))
        # Delete older logs if needed
        if max_logs > 0:
            dir_list = os.listdir(self.log_folder_path)
            while len(dir_list) > max_logs:
                older_file_number = float('inf')
                older_file = ''
                for file in dir_list:
                    if file.endswith('.log'):
                        try:
                            file_number = int(file[:-4])
                            if file_number < older_file_number:
                                older_file_number = file_number
                                older_file = file
                        except ValueError:
                            continue
                # Delete the older log
                if older_file:
                    os.remove(os.path.join(self.log_folder_path, older_file))
                    dir_list = os.listdir(self.log_folder_path)




