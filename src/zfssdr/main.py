import datetime
import subprocess
import time
import sys
import argparse

today = datetime.date.today().strftime("%Y%m%d")

class Datasets:
    """
    ZFS datasets from a host where this program is running.
    """

    def __init__(self, filter=None) -> None:
        # my datasets are named like this:
        # rpool/archlinux/data or rpool/archlinux/var/lib
        # I only deal with these datasets instead of their container
        # which look like rpool/archlinux or the whole pool rpool
        # so filter datasets with length of name equals 3 or 4
        if not filter:
            filter = (3, 4)
        self.filter = filter
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
        self.datasets = [dataset for dataset in self.all_datasets if len(dataset.split('/')) in self.filter]

    @staticmethod
    def is_data(dataset: str) -> bool:
        return dataset.startswith('dpool') or dataset.endswith('/home')

    def act(self, action: str, suffix: str) -> None:
        """
        Execute snapshots, destroy or rollback of filtered datasets.
        """
        datasets = self.datasets
        if not suffix:
            suffix = today
        try:
            action = self.actions[action]
        except:
            print('Invalid action.')
            sys.exit(1)
        if action == 'zfs rollback':
            datasets = [dataset for dataset in self.datasets if not self.is_data(dataset)]
        for dataset in datasets:
            snapshot = dataset + '@' + suffix
            command = action + ' ' + snapshot
            try:
                time.sleep(0.2)
                print(command)
                result = subprocess.run([command], shell=True)
            except Exception as e:
                print(e)
                print(f'Failed to {self.actions[action].split()[-1]} {snapshot}.')

def zfssdr(action='s', suffix=None, filter=(3, 4)):
    """
    Execute snapshots, destroy or rollback of filtered datasets.
    """
    datasets = Datasets(filter)
    datasets.act(action, suffix)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Execute snapshots, destroy or rollback of filtered datasets.')
    parser.add_argument('action', type=str, help='s: snapshot, d: destroy, r: rollback')
    parser.add_argument('-s', '--suffix', type=str, help='suffix of snapshot name')
    parser.add_argument('-f', '--filter', type=int, nargs=2, help='filter datasets with length of name equals filter[0] or filter[1]')
    args = parser.parse_args()
    zfssdr(args.action, args.suffix, args.filter)