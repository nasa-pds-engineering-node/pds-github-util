import os
from configparser import ConfigParser
from datetime import datetime
import logging
from pds_github_util.corral import CattleHead

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Herd:
    def __init__(self, gitmodules=None, dev=False, token=False):
        self._dev =dev
        self._token = token
        self._config = ConfigParser()
        if gitmodules:
            self._config.read(gitmodules)
        else:
            self._config.read(os.path.join(os.getcwd(), ".gitmodules"))

        self._gather_the_herd()

    def number_of_heads(self):
        return len(self._herd)

    def get_cattle_heads(self):
        return self._herd

    def _gather_the_herd(self):
        logger.info('gather the herd of submodules listed in .gitmodules')

        self._herd = {}
        self._shepard_version = None
        self._update_date = None
        for section in self._config.sections():
            if 'submodule "."' not in section:
                module_array = section.split(" ")
                if len(module_array) >= 2:
                    module_name = module_array[1].strip('"')
                else:
                    logger.error(f'section {section} is malformed, expected format is: [submodule "<module name>"]')

                optional_module_options = {k:self._config.get(section, k).strip("/") for k in ['version'] if self._config.has_option(section, k)}
                cattle_head = CattleHead(module_name,
                                                     self._config.get(section, "url").strip("/"),
                                                     dev=self._dev,
                                                     token=self._token,
                                                     **optional_module_options)

                pub_date = cattle_head.get_published_date()
                if pub_date:
                    self._update_date = max(self._update_date, pub_date) if self._update_date else pub_date
                self._herd[module_name] = cattle_head
            else:
                self._shepard_version = self._config.get(section, 'version')
                self._release_date = datetime.fromisoformat(self._config.get(section, 'release'))

        return 0

    def set_shepard_version(self, version):
        """
        For unit test purpose
        :param version:
        :return:
        """
        self._config['submodule "."']['version'] = version

    def get_shepard_version(self):
        return self._config.get('submodule "."', 'version').strip(" ")

    def get_release_datetime(self):
        return self._release_date

    def get_update_datetime(self):
        return self._update_date