import os
import mdutils
from datetime import datetime

SEMANTIC_VERSION_REGEX = r'\d+\.\d+(-SNAPSHOT)?'


def colored_datetime(d, colored=True, format='%Y-%m-%d'):
    d_str = d.strftime(format)
    if colored:
        color = 'orange' if d > datetime.now() else 'green'
        return f'<span style="color:{color}">{d_str}</span>'
    else:
        return d_str


class HerdTable:
    def __init__(self, columns):
        self.table = columns
        self.n_rows = 1
        self.n_columns = len(columns)

    def add_herd(self, h):
        v = h.get_shepard_version()
        build_link = f'[{v}](./{v})'
        self.table.extend([build_link,
                           colored_datetime(h.get_release_datetime()),
                           colored_datetime(h.get_update_datetime(), colored=False)])
        self.n_rows += 1

    def __len__(self):
        return self.n_rows - 1

    def write_to_md_file(self, md_file):
        md_file.new_table(columns=self.n_columns,
                          rows=self.n_rows,
                          text=self.table,
                          text_align='center')


def update_index(root_dir, herds, format='md'):

    index_file_name = os.path.join(root_dir, 'index.md')
    index_md_file = mdutils.MdUtils(file_name=index_file_name, title=f'PDS Engineering Node software suite, builds')

    herds.sort(key=lambda x: x.get_release_datetime(), reverse=True)
    herds_iterator = iter(herds)

    now = datetime.now()

    # dev/uit releases
    table_development_releases = HerdTable(["build", "planned release", "update"])
    while True:
        herd = next(herds_iterator)
        if herd.get_release_datetime() > now:
            table_development_releases.add_herd(herd)
        else:
            break

    # stable release
    table_latest_stable_release = HerdTable(["build", "release", "update"])
    table_latest_stable_release.add_herd(herd)

    # archived releases
    table_archived_releases = HerdTable(["build", "release", "update"])
    while True:
        try:
            herd = next(herds_iterator)
            table_archived_releases.add_herd(herd)
        except StopIteration as e:
            break

    if len(table_latest_stable_release):
        index_md_file.new_paragraph("Latest stable release:")
        index_md_file.new_line('')
        table_latest_stable_release.write_to_md_file(index_md_file)

    if len(table_development_releases):
        index_md_file.new_line('')
        index_md_file.new_paragraph("Development releases:")
        index_md_file.new_line('')
        table_development_releases.write_to_md_file(index_md_file)

    if len(table_archived_releases):
        index_md_file.new_line('')
        index_md_file.new_paragraph("Archived stable releases:")
        index_md_file.new_line('')
        table_archived_releases.write_to_md_file(index_md_file)

    img = index_md_file.new_inline_image('new PDS logo test', 'https://nasa-pds.github.io/pdsen-corral/images/logo.png')
    index_md_file.new_line(img)

    index_md_file.create_md_file()

