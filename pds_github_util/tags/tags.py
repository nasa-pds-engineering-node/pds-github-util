import github3
import git
from packaging import version



class Tags:
    JAVA_DEV_SUFFIX = '-SNAPSHOT'
    PYTHON_DEV_SUFFIX = '-dev'


    def __init__(self, org, repo, token=None):
        self._organization = org
        self._repository = repo

        gh = github3.login(token=token)
        self._repo = gh.repository(self._organization, self._repository)

        self.sorted_tags = []
        for tag in self._repo.tags():
            commit = self._repo.commit(tag.commit.sha)
            self.sorted_tags.append({'date': commit.as_dict()['commit']['author']['date'], 'name': tag.name})

        self.sorted_tags.sort(key=lambda t: t['date'])

    def get_earliest_tag_after(self, date_iso):
        for tag in self.sorted_tags:
            if tag['date'] > date_iso:
                return tag['name']

    def get_latest_tag(self, dev=False):
        latest_tag = None
        for tag in self._repo.tags():
            if Tags.is_dev_version(tag.name) and dev:  # if we have a dev version and we look for dev version
                latest_tag = Tags.get_max_tag(tag.name, latest_tag) if latest_tag else tag.name
            elif not (Tags.is_dev_version(tag.name) or dev):  # if we don't have a dev version and we look for stable version
                latest_tag = Tags.get_max_tag(tag.name, latest_tag) if latest_tag else tag.name

        return latest_tag.__str__() if latest_tag else None

    def get_tag(self, tag_name):
        for tag in self._repo.tags():
            if tag.name == tag_name:
                return tag

        return None

    @classmethod
    def is_dev_version(cls, tag_name):
        return tag_name.endswith(Tags.PYTHON_DEV_SUFFIX) or tag_name.endswith(Tags.PYTHON_DEV_SUFFIX)

    @staticmethod
    def get_max_tag(tag_name, other_tag_name):
        vers = version.parse(tag_name)
        other_vers = version.parse(other_tag_name)
        return tag_name if (vers > other_vers) else other_tag_name



