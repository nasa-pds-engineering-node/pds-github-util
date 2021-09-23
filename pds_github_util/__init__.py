from ._version import get_versions

__version__ = get_versions()["version"]
__date__ = get_versions()["date"]
del get_versions

from . import _version
__version__ = _version.get_versions()['version']
