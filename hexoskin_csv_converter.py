import sys, glob, os
import pandas as pd

def converter(dirpath=None):
    if dirpath is None:
        dirpath = 'hexoskin'

    filepaths = glob.glob(os.path.join(dirpath, '*.csv'))
    for filepath in filepaths:
        hexoskin_df = pd.read_csv(filepath)

        hexoskin_df['time [s/256]']



if __name__ == '__main__':
    if len(sys.argv) == 1:
        converter()
    elif len(sys.argv) == 2:
        converter(sys.argv[1])
    else:
        raise ValueError('Invalid arguments!: Usage: python {} [directory path]'.format(__file__))