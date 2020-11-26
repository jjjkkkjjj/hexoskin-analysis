import sys, glob, os, argparse
import pandas as pd
from time import mktime, gmtime
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='Convert hexoskin raw data into actual data.')
parser.add_argument('-i', '--input-dir', type=str, default=os.path.join('hexoskin', 'raw'),
                    help='Input directory path')
parser.add_argument('-o', '--output-dir', type=str, default=os.path.join('hexoskin', 'actual'),
                    help='Output directory path')

args = parser.parse_args()

def hexotime2date(hexoSeries):
    """
    :param hexoSeries: pd.Series, hexotime stamp
    :return: hexoSeries_date: pd.Series, date timestamp
    """
    def hexo2date(hexotime):
        # to seconds
        t = hexotime / 256
        # get seconds (struct_time) since 1970/1/1 in UTC, and then get local time in UTC
        t = mktime(gmtime(t))
        # convert datetime and add 9 hours which is Japan's offset for UTC finally
        return datetime.fromtimestamp(t) + timedelta(hours=9)
    return hexoSeries.apply(lambda x: hexo2date(x))



def converter():
    input_dirpath = args.input_dir
    output_dirpath = args.output_dir

    filepaths = glob.glob(os.path.join(input_dirpath, '*.xlsx'))
    for filepath in filepaths:
        hexoskin_df = pd.read_excel(filepath)

        ### convert hexotime into normal dates ###
        hexotimeSeries = hexoskin_df['time [s/256]']
        dates = hexotime2date(hexotimeSeries)
        # split dates into date and time
        hexoskin_df[['date', 'time']] = dates.astype(str).str.split(' ', expand=True)

        ### convert raw values into correct values ###
        # acc

        # save
        filename, _ = os.path.splitext(os.path.basename(filepath))
        savepath = os.path.join(output_dirpath, filename + '-converted.xlsx')

        hexoskin_df.to_excel(savepath)



if __name__ == '__main__':
    converter()