import configparser
import sys
sys.dont_write_bytecode=True
read_config = configparser.ConfigParser()
read_config.read("settings.ini")

token = read_config['settings']['token'].strip().replace(" ", "")

def get_admins():
    read_admins = configparser.ConfigParser()
    read_admins.read("settings.ini")
    admins = read_admins['settings']['admin_id'].strip().replace(" ", "")
    if "," in admins:
        admins = admins.split(",")
    else:
        if len(admins) >= 1:
            admins = [admins]
        else:
            admins = []
    while "" in admins: admins.remove("")
    while " " in admins: admins.remove(" ")
    while "\r" in admins: admins.remove("\r")
    while "\n" in admins: admins.remove("\n")
    admins = list(map(int, admins))
    return admins
