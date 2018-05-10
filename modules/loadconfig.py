from configparser import ConfigParser
from socket import gethostname
import git

class ExtConfigParser(ConfigParser):
    def getlist(self,section,option):
        value = self.get(section,option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self,section,option):
        return [int(x) for x in self.getlist(section,option)]


config = ExtConfigParser()
config.read('/etc/galaxymediatools.cfg')
hostname = gethostname()

g = git.cmd.Git('/opt/galaxymedia')
g.pull()

