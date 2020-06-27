import os
import mdutils
import re

SEMANTIC_VERSION_REGEX = r'\d+\.\d+(-SNAPSHOT)?'


def update_index(root_dir):
    index_file_name = os.path.join(root_dir, 'index.md')
    index_md_file = mdutils.MdUtils(file_name=index_file_name, title=f'PDS Engineering Node software suite, builds')
    index_md_file.new_inline_image('new PDS logo test', 'https://nasa-pds.github.io/pdsen-corral/images/logo.png')
    prog = re.compile(SEMANTIC_VERSION_REGEX)
    build_dirs = []
    for d in os.listdir(root_dir):
        if os.path.isdir(os.path.join(root_dir,d)) and prog.match(d):
            build_dirs.append(f'[{d}](./{d})')
    build_dirs.reverse()
    index_md_file.new_list(build_dirs)

    index_md_file.create_md_file()
