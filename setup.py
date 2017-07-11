#!/usr/bin/env python3

import subprocess
import os
import logging

if os.sys.version[0] != '3':
    print('Please use python3, not python2')
    os.sys.exit(1)


class Setup:
    def __init__(self, root_path):
        self.install_path = os.path.join(root_path, '.kinksorter')
        self.source_path = os.path.dirname(__file__)

    @staticmethod
    def _run_cmd(cmd):
        ret = subprocess.run(cmd, stderr=subprocess.PIPE)
        if ret.returncode:
            logging.error('Command {0} failed, error was: "{1}"'.format(cmd, ret.stderr))
            return False
        return True

    def install(self):
        if not os.path.exists(self.install_path):
            os.makedirs(self.install_path, exist_ok=True)

        try:
            if self._install_virtualenv() and self._install_requirements() and \
               self._install_src() and self._install_kinkyapi():
                logging.info('Installation complete!')
                return True
        except KeyboardInterrupt:
            return False

    def _install_virtualenv(self):
        logging.info('Setting up the virtualenv...')
        if not os.path.exists(os.path.join(self.install_path, 'virtualenv')):
            cmd = ["python3", "-m", "venv", os.path.join(self.install_path, 'virtualenv')]
            if not self._run_cmd(cmd):
                return False

        return True

    def _install_requirements(self):
        logging.info('  Satisfying python package requirements...')

        pip = os.path.join(self.install_path, "virtualenv", "bin", "pip")
        requirements = os.path.join(self.source_path, 'requirements.txt')
        if not self._run_cmd([pip, 'install', '-r', requirements]):
            logging.warning('Some requirements are still unsatisfied!')
            return False

        return True

    def _install_src(self):
        logging.info('Installing the kinksorter at the location...')
        installed_source_path = os.path.join(self.install_path, 'src')
        if not os.path.exists(installed_source_path):
            cmd = ["cp", "-r", os.path.join(self.source_path, 'src'), installed_source_path]
            if not self._run_cmd(cmd):
                return False

        return True

    def _install_kinkyapi(self):
        logging.info('Making sure the KinkyAPI is up-to-date...')
        kinkcom_db_gz = os.path.join(self.install_path, "src", "kinksorter_app", "apis", "kinkcom", "kinkyapi.db.gz")
        if not os.path.exists(kinkcom_db_gz[:-3]):
            cmd = ["wget", "-O", kinkcom_db_gz, "https://www.kinkyapi.site/kinkcom/dump_sqlite"]
            if not self._run_cmd(cmd):
                return False
            self._run_cmd(["gunzip", kinkcom_db_gz])

        return True

    def uninstall(self):
        if not os.path.exists(self.install_path):
            logging.info('There is no kinksorter installation at "{0}"!'.format(self.install_path))
            return

        if self._run_cmd(["rm", "-r", self.install_path]):
            logging.info('Uninstall complete!')
        else:
            logging.info('Uninstall failed')

    def start(self):
        os.system("/bin/bash -c 'source {0} && python3 {1} migrate -v0 && python3 {1} runserver'".format(
                                                            os.path.join(self.install_path, "virtualenv/bin/activate"),
                                                            os.path.join(self.install_path, 'src', 'manage.py')))


if __name__ == '__main__':
    import argparse
    from os import path, access, W_OK, R_OK

    def argcheck_dir(string):
        if path.isdir(string) and access(string, W_OK) and access(string, R_OK) or\
           path.isdir(path.dirname(string)) and access(path.dirname(string), W_OK):
            return path.abspath(string)
        raise argparse.ArgumentTypeError('%s is no directory or isn\'t writeable' % string)

    argparser = argparse.ArgumentParser(description="Easy porn storage combining via webinterface")
    argparser.add_argument('-r', '--remove', action='store_true',
                           help='What to do? (install, uninstall, start)')
    argparser.add_argument('root_path', type=argcheck_dir, metavar="destination",
                           help='Set the path where the sorted storage should be created')

    args = argparser.parse_args()

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    setup = Setup(args.root_path)
    if args.remove:
        setup.uninstall()
    else:
        setup.install() and setup.start()
