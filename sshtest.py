#!/usr/bin/python3

from pexpect import pxssh
from wakeonlan import send_magic_packet as wol


def remote_cmd(server,username,password,cmd):
    ssh = pxssh.pxssh()

    try:
        ssh.login(server,username,password)
    except pxssh.ExceptionPexpect as e:
        print('Failed to connect to remote server with SSH')
        return False
    else:
        print('SSH connected to remote server [{}]'.format('server'))
        try:
            ssh.sendline(cmd)
            ssh.prompt()
            ssh.sendline('echo $?')
            ssh.prompt()
            splitres = ssh.before.decode().split('\r\n')
            result = splitres[1]
        except:
            print('SSH remote command execution failed')
            return False
        else:
            print('SSH remote command executed successfully')
            return result

def wakeup(macaddr):
    wol(macaddr)


#print(remote_cmd('172.25.1.26','ip','Ifa6wasa9','lirs'))

