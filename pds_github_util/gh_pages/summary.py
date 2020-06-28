import os
import logging
from mdutils import MdUtils
from pds_github_util.corral.herd import Herd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLUMNS = ['download', 'manual', 'changelog', 'requirements', 'license', 'feedback']

def write_build_summary(gitmodules=None, root_dir='.', output_file_name=None, token=None, dev=False, version=None):

    herd = Herd(gitmodules=gitmodules, dev=dev, token=token)

    if version is None:
        version = herd.get_shepard_version()
    else:
        # for unit test
        herd.set_shepard_version(version)

    logger.info(f'build version is {version}')
    if dev and not ('dev' in version or 'SNAPSHOT' in version):
        logger.error("version of build does not contain dev or SNAPSHOT, dev build summary is not generated")
        exit(1)
    elif not dev and ('dev' in version or 'SNAPSHOT' in version):
        logger.error("version of build contains dev or SNAPSHOT, release build summary is not generated")
        exit(1)

    if not output_file_name:
        output_file_name = os.path.join(root_dir, version, 'index')
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)

    software_summary_md = MdUtils(file_name=output_file_name, title=f'Software Summary (build {version})')

    column_headers = []
    for column in COLUMNS:
        column_headers.append(f'![{column}](https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png)')

    table = ["tool", "version", "description", *column_headers]
    n_columns = len(table)
    for k, ch in herd.get_cattle_heads().items():
        table.extend(ch.get_table_row())
    software_summary_md.new_table(columns=n_columns,
                                  rows=herd.number_of_heads()+1,
                                  text=table,
                                  text_align='center')

    software_summary_md.create_md_file()

    return os.path.dirname(output_file_name)
