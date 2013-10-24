# -*- coding: utf-8 -*-

import requests

from ..common.subject import Subject


class BaseClass(Subject):
    """A common base class providing logging and desktop-notification.
    """
    def emit(self, message):
        """
        sends message to the notifier
        """
        self.notify_observers(event='Dynamic DNS', msg=message)


class UpdateProtocol(BaseClass):
    """the base class for all update protocols"""
    updateurl = None
    theip = None
    hostname = None  # this holds the desired dns hostname
    status = 0
    nochgcount = 0
    failcount = 0

    def success(self):
        self.status = 0
        self.failcount = 0
        self.nochgcount = 0
        #self.emit("Updated IP address of '%s' to %s" % (self.hostname, self.theip))

    def abuse(self):
        self.status = 1
        self.failcount = 0
        self.nochgcount = 0
        #self.emit("This client is considered to be abusive for hostname '%s'" % (self.hostname))

    def nochg(self):
        self.status = 0
        self.failcount = 0
        self.nochgcount += 1

    def nohost(self):
        self.status = 1
        self.failcount += 1
        self.emit("Invalid/non-existant hostname: [%s]" % (self.hostname))
        self.status = "nohost"

    def failure(self):
        self.status = 1
        self.failcount += 1
        self.emit("Service is failing!")

    def notfqdn(self):
        self.status = 1
        self.failcount += 1
        self.emit("The provided hostname '%s' is not a valid hostname!" % (self.hostname))

    def protocol(self):
        if hasattr(self, '_protocol'):
            return self._protocol()

        params = {'myip': self.theip, 'hostname': self.hostname}
        r = requests.get(self.updateUrl(), params=params, auth=(self.userid, self.password))
        if r.status_code == 200:
            if r.text.startswith("good "):
                self.success()
                return self.theip
            elif r.text == 'nochg':
                self.nochg()
                return self.theip
            elif r.text == 'nohost':
                self.nohost()
                return 'nohost'
            elif r.text == 'abuse':
                self.abuse()
                return 'abuse'
            elif r.text == '911':
                self.failure()
                return '911'
            elif r.text == 'notfqdn':
                self.notfqdn()
                return 'notfqdn'
            else:
                self.status = 1
                self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.theip, r.text))
                return 'invalid dyndns protocol response: %s' % r.text
        else:
            self.status = 1
            self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.theip, r.status_code))
            return 'invalid http status code: %s' % r.status_code


class UpdateProtocolDummy(UpdateProtocol):

    updateurl = "http://localhost.nonexistant/nic/update"

    def __init__(self, options=None):
        if options is None:
            self._options = {}
        else:
            self._options = options
        super(UpdateProtocolDummy, self).__init__()

    @staticmethod
    def configuration_key():
        return "dummy"

    @staticmethod
    def updateUrl():
        return UpdateProtocolDummy.updateurl

    def update(self, ip):
        return ip


class UpdateProtocolMajimoto(UpdateProtocol):
    """This class contains the logic for talking to the update service of dyndns.majimoto.net"""

    updateurl = "https://dyndns.majimoto.net/nic/update"

    def __init__(self, protocol_options):
        self.key = protocol_options['key']
        self.hostname = protocol_options['hostname']
        self.theip = None

        self.failcount = 0
        self.nochgcount = 0
        super(UpdateProtocolMajimoto, self).__init__()

    def update(self, ip):
        self.theip = ip
        return self.protocol()

    def _protocol(self):
        params = {'myip': self.theip, 'key': self.key, 'hostname': self.hostname}
        r = requests.get(self.updateUrl(), params=params)
        if r.status_code == 200:
            if r.text == 'good':
                self.success()
            elif r.text == 'nochg':
                self.nochg()
            elif r.text == 'nohost':
                self.nohost()
            elif r.text == 'abuse':
                self.abuse()
            elif r.text == '911':
                self.failure()
            elif r.text == 'notfqdn':
                self.notfqdn()
            else:
                self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.theip, r.text))
        else:
            self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.theip, r.status_code))

    @staticmethod
    def configuration_key():
        return "majimoto"

    @staticmethod
    def updateUrl():
        return UpdateProtocolMajimoto.updateurl


class UpdateProtocolDyndns(UpdateProtocol):
    """Protocol handler for dyndns.com"""

    updateurl = "https://members.dyndns.org/nic/update"

    def __init__(self, protocol_options):
        self.hostname = protocol_options['hostname']
        self.userid = protocol_options['userid']
        self.password = protocol_options['password']

        self.failcount = 0
        self.nochgcount = 0
        super(UpdateProtocolDyndns, self).__init__()

    @staticmethod
    def configuration_key():
        return "dyndns"

    @staticmethod
    def updateUrl():
        return UpdateProtocolDyndns.updateurl

    def update(self, ip):
        self.theip = ip
        return self.protocol()


class UpdateProtocolNoip(UpdateProtocol):
    """Protocol handler for www.noip.com"""

    updateurl = "https://dynupdate.no-ip.com/nic/update"

    def __init__(self, options):
        self.theip = None
        self.hostname = options['hostname']
        self.userid = options['userid']
        self.password = options['password']

        self.status = 0
        self.failcount = 0
        self.nochgcount = 0
        super(UpdateProtocolNoip, self).__init__()

    @staticmethod
    def configuration_key():
        return "noip"

    @staticmethod
    def updateUrl():
        return UpdateProtocolNoip.updateurl

    def update(self, ip):
        self.theip = ip
        return self.protocol()