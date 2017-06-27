#!/usr/bin/env python3

import subprocess
import os


class Setup:
    def __init__(self, root_path):
        self.root_path = root_path = os.path.join(root_path, '.kinksorter')

    def install(self):
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path, exist_ok=True)

        kinkcom_db = os.path.join(self.root_path, "src", "kinksorter_app", "apis", "kinkcom", "kinkyapi.db.gz")
        commands = [
            ["python3", "-m", "venv", os.path.join(self.root_path, 'virtualenv')],
            ["cp", "--exclude=kinksorter.db", "-r", os.path.join(os.path.dirname(__file__), "src"), self.root_path],
            ["wget", "-O", kinkcom_db, "https://www.kinkyapi.site/kinkcom/dump_sqlite" ],
            ["gunzip", kinkcom_db]
        ]
        for command in commands:
            print('Running:', ' '.join(command))
            ret = subprocess.run(command, stderr=subprocess.PIPE)
            if ret.returncode:
                print('Command failed, error was: "{}"'.format(ret.stderr))
                self.uninstall()
                return

        print('Installation complete!')

    def uninstall(self):
        if not os.path.exists(self.root_path):
            print('There is no kinksorter installation at "{}"!'.format(self.root_path))
            return

        ret = subprocess.run(["rm", "-r", self.root_path], stderr=subprocess.PIPE)
        if not ret.returncode:
            print('Uninstall complete!')
        else:
            print('Uninstall failed, error: "{}"'.format(ret.stderr))

    def start(self):
        os.system("cd {} && sh virtualenv/bin/activate && cd {} && "
                  "python3 manage.py migrate && python3 manage.py runserver".format(
            self.root_path,
            os.path.join(self.root_path, 'src')))


if __name__ == '__main__':
    import argparse
    from os import path, access, W_OK, R_OK

    def argcheck_dir(string):
        if path.isdir(string) and access(string, W_OK) and access(string, R_OK) or\
           path.isdir(path.dirname(string)) and access(path.dirname(string), W_OK):
            return path.abspath(string)
        raise argparse.ArgumentTypeError('%s is no directory or isn\'t writeable' % string)

    argparser = argparse.ArgumentParser(description="Easy Porn storage combining via webinterface")
    argparser.add_argument('action', choices=['install', 'uninstall', 'start'], metavar="action",
                           help='What to do? (install, uninstall, start)')
    argparser.add_argument('root_path', type=argcheck_dir, metavar="destination",
                           help='Set the path where the sorted storage should be created')

    args = argparser.parse_args()

    setup = Setup(args.root_path)
    getattr(setup, args.action)()
