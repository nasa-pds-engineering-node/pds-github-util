import os
import mdutils
from datetime import datetime

SEMANTIC_VERSION_REGEX = r'\d+\.\d+(-SNAPSHOT)?'


def colored_datetime(d, colored=True, format='%Y-%m-%d'):
    d_str = d.strftime(format)
    if colored:
        color =  'orange' if d>datetime.now() else 'green'
        return f'<span style="color:{color}">{d_str}</span>'
    else:
        return d_str


def update_index(root_dir, herds):
    index_file_name = os.path.join(root_dir, 'index.md')
    index_md_file = mdutils.MdUtils(file_name=index_file_name, title=f'PDS Engineering Node software suite, builds')

    table = ["build" , "release", "update"]
    herds.sort(key=lambda x: x.get_release_datetime(), reverse=True)
    n_columns = len(table)
    for herd in herds:
        v = herd.get_shepard_version()
        build_link = f'[{v}](./{v})'
        table.extend([build_link,
                     colored_datetime(herd.get_release_datetime()),
                     colored_datetime(herd.get_update_datetime(), colored=False)])

    index_md_file.new_table(columns=n_columns,
                            rows=len(herds)+1,
                            text=table,
                            text_align='center')

    img = index_md_file.new_inline_image('new PDS logo test', 'https://nasa-pds.github.io/pdsen-corral/images/logo.png')
    index_md_file.new_line(img)

    index_md_file.create_md_file()
