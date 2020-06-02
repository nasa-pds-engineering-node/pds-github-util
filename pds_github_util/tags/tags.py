import github3



class Tags:
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



