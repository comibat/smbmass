#!/usr/bin/python


import sys
import subprocess
import re
import getpass


class COLOR:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[91m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    

def usage():
    print("""
    Usage:
    \t{} <local_mounting_point_root ex: /media/tmp> <smb_share, ex: //10.1.2.3> <username> <domain, ex: google.com> [<password>]
    NOTE: <local_mounting_point_root> must exists, so please create it before starting the script.
    """.format(sys.argv[0]))
    exit(-1)


def get_shares(host, username, domain, password):
    shares = [] # list of triples: (sharename, type, comment)
    try:
        passwd = subprocess.Popen(('echo', password), stdout=subprocess.PIPE)
        output = subprocess.check_output(['smbclient', '-L', host, '-W', domain, '-U', username], stdin=passwd.stdout)
        output_decoded = output.decode('utf-8')
        print ("[+] found the following shares:\n{}".format(output_decoded[2:]))
        output_lines = output_decoded.splitlines()
        for line in output_lines[4:]:
            m = re.search('^\s+(.*?)\s+(.*?)\s+(.*)$', line)
            if m:
                share_name = m.group(1)
                share_type = m.group(2)
                share_comment = m.group(3)
                shares.append((share_name, share_type, share_comment),)
    except Exception as e:
        print (COLOR.FAIL+"[-] {}".format(e)+COLOR.ENDC)
        exit(-1)
    return shares


def create_mounting_point(mounting_point_root, nice_share_name):
    dir_to_make = ""
    try:
        dir_to_make = (mounting_point_root + nice_share_name if mounting_point_root[-1] == '/' else mounting_point_root + "/" + nice_share_name)
        subprocess.check_output(['mkdir', dir_to_make])
    except Exception as e:
        print (COLOR.FAIL+"[-] {}".format(e)+COLOR.ENDC)
        pass
    return dir_to_make


def mount_all_shares(mounting_point_root, host, username, domain, password, shares):
    for share in shares:
        share_name, share_type, share_comment = share
        nice_share_name = share_name.replace("$","_s")
        created_dir = create_mounting_point(mounting_point_root, nice_share_name)
        try:
            subprocess.check_output(["mount", "-t", "cifs", host+share_name, created_dir, "-o", "username="+username+",password="+password+",domain="+domain])
            print (COLOR.OKGREEN+"[+] mounted: {} -> {}".format(host+share_name, created_dir)+COLOR.ENDC)
            with open('umount_all.sh', 'a+') as f:
                f.write("umount {}\n".format(created_dir))
                f.flush()
        except Exception as e:
            print (COLOR.FAIL+"[-] {}".format(e)+COLOR.ENDC)
            pass           


def main():
    len(sys.argv) < 5 and usage()
    mounting_point_root = sys.argv[1]
    host = (sys.argv[2] if sys.argv[2][-1] == '/' else sys.argv[2] + "/")
    username = sys.argv[3]
    domain = sys.argv[4]
    password = ""
    try:
        password = sys.argv[5]
    except:
        password = getpass.getpass(prompt="Password: ")
    shares = get_shares(host,username,domain,password) # list of triples: (sharename, type, comment)
    mount_all_shares(mounting_point_root, host, username, domain, password, shares)

if __name__ == "__main__":
    main()