import os, time

def create_path(base_path, oper_name, device_list_file):
    timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
    dir_name = base_path + '/' + 'dumped_files/' + oper_name + '/' + \
        device_list_file + '_' + timestr + '/'
    os.makedirs(os.path.dirname(dir_name), exist_ok=True)

    return dir_name