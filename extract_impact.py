import sys, glob, os, argparse
import pandas as pd
import numpy as np
from time import mktime, gmtime
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='Convert hexoskin raw data into actual data.')
parser.add_argument('duration', type=int, default=10, help='Duration time to impact[s]')
parser.add_argument('-i', '--input-dir', type=str, default=os.path.join('hexoskin', 'actual'),
                    help='Input directory path')
parser.add_argument('-o', '--output-dir', type=str, default=os.path.join('hexoskin', 'impact'),
                    help='Output directory path')
parser.add_argument('-f', '--import-file', type=str, default=os.path.join('hexoskin', 'impact', 'impact-time.xlsx'),
                    help='Import file')

args = parser.parse_args()

def extract_impact():
    duration_time = args.duration
    input_dirpath = args.input_dir
    output_dirpath = args.output_dir
    import_file = args.import_file


    def extractor(column, filename, data_df, ret_df):
        """
        :param column: str, column name
        :param filename: str, filename
        :param ret_df: pd.DataFrame, appended extracted data for row
        :return:
        """
        # get index
        ind = data_df['time'][data_df['time'] == column].index[0]
        # get heart-rate
        hr = data_df.iloc[:, [6]][ind - duration_time + 1:ind + 1]

        # rename index
        rename = {ind: c for c, ind in enumerate(hr.index)}

        # get hr
        hr_numpy = hr.values.squeeze()

        # append filename to first row
        hr.loc[-1] = filename

        # sort index, filename is first
        hr = hr.reindex(index=np.roll(hr.index, 1))
        # do rename
        rename[-1] = 'filename'
        hr = hr.rename(rename, axis='index')

        # append average and std
        hr.loc['average'] = hr_numpy.mean()
        hr.loc['std'] = hr_numpy.std()

        ret_df = ret_df.append(hr.T, ignore_index=True)

        return ret_df

    def extract_loop(search_word):
        """
        :param search_word: str, searching word
        :return:
        """
        # parse import file
        impact_time_df = pd.read_excel(import_file)
        indices = impact_time_df.index[impact_time_df['filename'].str.contains(search_word)]

        df05, df15, df30, df60 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        for index in indices:
            row_series = impact_time_df.loc[index]
            filename = row_series['filename']
            path = os.path.join(input_dirpath, filename + '-converted.xlsx')
            data_df = pd.read_excel(path)

            # 0.5m
            df05 = extractor(str(row_series['0.5m time']), filename, data_df, df05)

            # 1.5m
            df15 = extractor(str(row_series['1.5m time']), filename, data_df, df15)

            # 3.0m
            df30 = extractor(str(row_series['3.0m time']), filename, data_df, df30)

            # 6.0m
            df60 = extractor(str(row_series['6.0m time']), filename, data_df, df60)

        df05.to_excel(os.path.join(output_dirpath, search_word + '-05-impact.xlsx'), index=False)
        df15.to_excel(os.path.join(output_dirpath, search_word + '-15-impact.xlsx'), index=False)
        df30.to_excel(os.path.join(output_dirpath, search_word + '-30-impact.xlsx'), index=False)
        df60.to_excel(os.path.join(output_dirpath, search_word + '-60-impact.xlsx'), index=False)

    extract_loop('nov')
    extract_loop('pro')

    return


if __name__ == '__main__':
    extract_impact()