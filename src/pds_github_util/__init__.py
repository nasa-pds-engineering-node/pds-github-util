import pkg_resources

__version__ = pkg_resources.resource_string(__name__, "VERSION.txt").decode("utf-8").strip()
