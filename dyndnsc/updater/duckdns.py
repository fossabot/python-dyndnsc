# -*- coding: utf-8 -*-

"""Module containing the logic for updating DNS records using the duckdns protocol.

From the duckdns.org website:

https://{DOMAIN}/update?domains={DOMAINLIST}&token={TOKEN}&ip={IP}

where:
    DOMAIN the service domain
    DOMAINLIST is either a single domain or a comma separated list of domains
    TOKEN is the API token for authentication/authorization
    IP is either the IP or blank for auto-detection

"""

from logging import getLogger

import requests

from .base import UpdateProtocol
from ..common import constants

LOG = getLogger(__name__)


class UpdateProtocolDuckdns(UpdateProtocol):
    """Updater for services compatible with the duckdns protocol."""

    def __init__(self, hostname, token, url, *args, **kwargs):
        """
        Initialize.

        :param hostname: the fully qualified hostname to be managed
        :param token: the token for authentication
        :param url: the API URL for updating the DNS entry
        """
        self.hostname = hostname
        self.token = token
        self._updateurl = url

        super(UpdateProtocolDuckdns, self).__init__()

    @staticmethod
    def configuration_key():
        """Return 'duckdns', identifying the protocol."""
        return "duckdns"

    def update(self, ip):
        """Update the IP on the remote service."""
        timeout = 60
        LOG.debug("Updating '%s' to '%s' at service '%s'", self.hostname, ip, self.url())
        params = {"domains": self.hostname.partition(".")[0], "token": self.token}
        if ip is None:
            params["ip"] = ""
        else:
            params["ip"] = ip
        # LOG.debug("Update params: %r", params)
        try:
            req = requests.get(self.url(), params=params, headers=constants.REQUEST_HEADERS_DEFAULT,
                               timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            LOG.warning("an error occurred while updating IP at '%s'",
                        self.url(), exc_info=exc)
            return False
        else:
            req.close()
        LOG.debug("status %i, %s", req.status_code, req.text)
        # TODO: duckdns response codes seem undocumented...
        if req.status_code == 200:
            if req.text.startswith("OK"):
                return ip
            return req.text
        return "invalid http status code: %s" % req.status_code
