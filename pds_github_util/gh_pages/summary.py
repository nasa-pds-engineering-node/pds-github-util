import os
import logging
from mdutils import MdUtils
from pds_github_util.tags.tags import Tags
from pds_github_util.corral.herd import Herd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLUMNS = ['manual', 'changelog', 'requirements', 'download', 'license', 'feedback']

def write_build_summary(gitmodules=None, root_dir='.', output_file_name=None, token=None, dev=False, version=None):

    herd = Herd(gitmodules=gitmodules, dev=dev, token=token)

    if version is None:
        version = herd.get_shepard_version()
    else:
        # for unit test
        herd.set_shepard_version(version)

    logger.info(f'build version is {version}')
    is_dev = Tags.JAVA_DEV_SUFFIX in version or Tags.PYTHON_DEV_SUFFIX in version
    if dev and not is_dev:
        logger.error(f'version of build does not contain {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, dev build summary is not generated')
        exit(1)
    elif not dev and is_dev:
        logger.error(f'version of build contains {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, release build summary is not generated')
        exit(1)

    if not output_file_name:
        output_file_name = os.path.join(root_dir, version, 'index')
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)

    software_summary_md = MdUtils(file_name=output_file_name, title=f'Software Summary (build {version})')

    column_headers = []
    for column in COLUMNS:
        column_headers.append(f'![{column}](https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png)')

    table = ["tool", "version", "last updated", "description", *column_headers]
    n_columns = len(table)
    for k, ch in herd.get_cattle_heads().items():
        table.extend(ch.get_table_row())
    software_summary_md.new_table(columns=n_columns,
                                  rows=herd.number_of_heads()+1,
                                  text=table,
                                  text_align='center')

    software_summary_md.create_md_file()

    return herd
