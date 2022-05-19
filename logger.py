import os
from datetime import datetime


class Logger:
    def __init__(self, debug=False):
        self.log_folder_path = os.path.join(os.getcwd(), "logs")
        self.curr_log_path = os.path.join(self.log_folder_path, datetime.now().strftime("%Y%m%d%H%M%S.log"))
        self.logs = []
        self.debug = debug
        self.next_line = True

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
            os.mkdir(self.log_folder_path)
        f = open(self.curr_log_path, 'w', encoding='UTF8')
        f.write("\n".join(self.logs))
        f.close()
        if max_logs > 0:
            dir_list = os.listdir(self.log_folder_path)
            while len(dir_list) > max_logs:
                older_file_number = int(dir_list[0][:-4])
                for file in dir_list:
                    if older_file_number > int(dir_list[0][:-4]):
                        older_file_number = int(dir_list[0][:-4])
                os.remove(os.path.join(self.log_folder_path, str(older_file_number) + ".log"))
                dir_list = os.listdir(self.log_folder_path)



