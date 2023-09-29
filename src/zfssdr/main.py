#!/usr/bin/env python3

import datetime
import subprocess
import time
import sys
import argparse
import glob

today = datetime.date.today().strftime("%Y%m%d")
CACHE_DIRS = ['/var/cache/pacman/pkg', '$HOME/.cache/paru/clone', '/home/han/.cache/paru/clone']

def reversed_count(n=5):
    for i in reversed(range(1, n+1)):
        print(i)
        time.sleep(1)

def clear_cache(CACHE_DIRS):
    for cache_dir in CACHE_DIRS:
        print(f'Clearing cache in {cache_dir} ...')
        # the trailing glob * need shell to expand to file names
        # use glob to expand file names
        # check=True will make the method throwing exception if
        # a non-zero exit code is returned
        subprocess.run(['rm', '-rf'] + glob.glob(f'{cache_dir}/*'), check=True)


class Datasets:
    """
    ZFS datasets from a host where this program is running.
    """

    def __init__(self):
        # my datasets are named like this:
        # rpool/archlinux/data or rpool/archlinux/var/lib
        # I only deal with these datasets instead of their containers
        # which look like rpool/archlinux or the whole pool (like rpool, dpool)
        self.actions = {'s': 'sudo zfs snapshot',
                        'd': 'sudo zfs destroy',
                        'r': 'sudo zfs rollback'}
        # get names of all datasets
        # zfs list -o name
        result = subprocess.run(['zfs', 'list', '-o', 'name'], capture_output=True)
        if result.returncode != 0:
            print('Failed to list datasets')
            sys.exit(1)
        self.all_datasets  = result.stdout.decode('utf-8').strip().split('\n')[1:]

    def datasets(self, filter=None):
        return self._filter(filter)

    def _filter(self, filter):
        if filter is None:
            # get datasets with length of name split by '/' equals 3 or 4
            filter = (3, 4)
        try:
            datasets = [dataset for dataset in self.all_datasets if len(dataset.split('/')) in filter]
            if datasets:
                return datasets
            return
        except:
            return

    def is_data(self, dataset):
        return self._is_data(dataset)

    def _is_data(self, dataset):
        # dataset with name starts with 'dpool' or ends with '/home'
        # is considered as a dataset for data which will not be
        # rollback under system rollback circumstance
        return dataset.startswith('dpool') or dataset.endswith('/home') or dataset.endswith('data')

    def act(self, action, suffix, filter):
        """
        Execute snapshots, destroy or rollback of filtered datasets.
        """
        datasets = self.datasets(filter)
        if not suffix:
            suffix = today
        try:
            action = self.actions[action]
            action_primitive = action.split()[-1]
        except KeyError as e:
            print('Invalid action. Support actions: s, d, r')
            sys.exit(1)
        # don't rollback datasets which are data
        if action_primitive == 'rollback':
            datasets = [dataset for dataset in datasets if not self.is_data(dataset)]
        if action_primitive == 'snapshot':
            clear_cache(CACHE_DIRS)
        snapshots = []
        for dataset in datasets:
            snapshots.append(dataset + '@' + suffix)
        print(f'Performing {action_primitive} on {len(datasets)} datasets(snapshots) in 5 seconds:')
        for snapshot in snapshots:
            print(f'{str.capitalize(action_primitive)} {snapshot}')
        print('\n')
        reversed_count(5)
        for snapshot in snapshots:
            command = action + ' ' + snapshot
            try:
                time.sleep(0.2)
                print(command)
                result = subprocess.run([command], shell=True)
                if result.returncode != 0:
                    print(f'Failed to {action_primitive} {snapshot}.')
            except Exception as e:
                print(e)

def zfssdr(action='s', suffix=None, filter=(3, 4)):
    """
    Execute snapshots, destroy or rollback of filtered datasets.
    """
    ds = Datasets()
    ds.act(action, suffix, filter)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Execute snapshots, destroy or rollback of filtered datasets.')
    parser.add_argument('action', type=str, help='s: snapshot, d: destroy, r: rollback')
    parser.add_argument('-s', '--suffix', type=str, help='suffix of snapshot name')
    parser.add_argument('-f', '--filter', type=int, nargs=2, help='filter datasets with length of name equals filter[0] or filter[1]')
    args = parser.parse_args()
    zfssdr(args.action, args.suffix, args.filter)
