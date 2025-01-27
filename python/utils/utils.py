
def parse_device_data(data, device):
    if type(data['devices'][device]) is dict:
        name = data['devices'][device].get('name') or device
        ip = data['devices'][device].get('ip') or data['devices'][device].get('console') or device
        console = data['devices'][device].get('console')
        user = data['devices'][device].get('user') or data['user']
        password = data['devices'][device].get('password') or data['password']
    else:
        name = device
        ip = device
        console = device
        user = data['user']
        password = data['password']
    return name, ip, console, user, password