from bs4 import BeautifulSoup
import logging
import re
import requests
import sys


class BackupClient:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._log = None
        self._groups = None

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()
        self.session.close()

    def login(self):
        self.log.info("Logging In")
        res = self.session.post('http://forums.e-democracy.org/login.html', {
            'login': self.username,
            'password': self.password
        })
        self.log.info("\tResponse Code: %s" % res.status_code)

    def logout(self):
        self.log.info("Logging Out")
        res = self.session.get('http://forums.e-democracy.org/logout.html')
        self.log.info("\tResponse Code: %s" % res.status_code)
        self.log.debug("Response Text: %s" % res.text)

    @property
    def log(self):
        if self._log is None:
            self._log = logging.getLogger(__name__)
            self._log.setLevel(logging.INFO)
            stdout = logging.StreamHandler(sys.stdout)
            stdout.setLevel(logging.INFO)
            self._log.addHandler(stdout)

        return self._log

    @property
    def groups(self):
        """Fetches the list of currently available groups from the E-Democracy
        group list."""

        if self._groups is None:
            links_page = self.session \
                             .get('http://forums.e-democracy.org/groups/')
            soup = BeautifulSoup(links_page.text, 'html.parser')
            links = soup.find(id='bodyblock') \
                        .find_all('a', href=re.compile("^/groups/"))
            self._groups = list(set(
                [link.get('href').split('/')[2] for link in links
                 if not link.get('href').startswith('/groups/leave.html')]
            ))
            self._groups.sort()

        return self._groups

if __name__ == '__main__':
    username = input('Username: ')
    password = input('Password: ')

    with BackupClient(username, password) as client:
        client.log.info(client.groups)
