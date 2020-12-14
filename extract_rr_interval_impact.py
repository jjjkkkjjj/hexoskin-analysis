import sys, glob, os, argparse
import pandas as pd
import numpy as np
from time import mktime, gmtime
from datetime import datetime, timedelta, date

parser = argparse.ArgumentParser(description='Convert hexoskin raw data into hr data.')
parser.add_argument('duration', type=int, default=10, help='Duration time to impact-hr[s]')
parser.add_argument('-ihr', '--input-hr-dir', type=str, default=os.path.join('hexoskin', 'hr'),
                    help='Input heart rate directory path')
parser.add_argument('-irr', '--input-rr-dir', type=str, default=os.path.join('hexoskin', 'rr_interval'),
                    help='Input rr interval directory path')
parser.add_argument('-o', '--output-dir', type=str, default=os.path.join('hexoskin', 'impact-rr_interval'),
                    help='Output directory path')
parser.add_argument('-f', '--import-file', type=str, default=os.path.join('hexoskin', 'impact-time.xlsx'),
                    help='Import file')

args = parser.parse_args()

def extract_impact():
    duration_time = args.duration
    input_hr_dirpath = args.input_hr_dir
    input_rr_interval_dirpath = args.input_rr_dir
    output_dirpath = args.output_dir
    import_file = args.import_file


    def extractor(column, filename, data_rr_interval_df, data_hr_df, ret_df):
        """
        :param column: str, column name
        :param filename: str, filename
        :param data_rr_interval_df: pd.DataFrame, heart rate dataframe
        :param data_hr_df: pd.DataFrame, heart rate dataframe
        :param ret_df: pd.DataFrame, appended extracted data for row
        :return:
        """
        # get start time
        diff = datetime.combine(date.today(), datetime.strptime(column, '%H:%M:%S').time()) - \
               datetime.combine(date.today(), datetime.strptime(data_hr_df.time[0], '%H:%M:%S').time())
        diff = diff.total_seconds()

        # get index with nearest time
        # ref https://stackoverflow.com/questions/30112202/how-do-i-find-the-closest-values-in-a-pandas-series-to-an-input-number
        impact_ind = (data_rr_interval_df['time [s]'] - diff).abs().argsort()[0]
        duration_time_ind = (data_rr_interval_df['time [s]'] - (diff - duration_time)).abs().argsort()[0]

        # get rr interval
        rr_interval = data_rr_interval_df.iloc[:, [1]][duration_time_ind:impact_ind + 1] / 256

        # rename index
        rename = {ind: c for c, ind in enumerate(rr_interval.index)}
        rr_interval = rr_interval.rename(rename, axis='index')

        # get hr
        rr_interval_numpy = rr_interval.values.squeeze()

        # append filename to first row
        rr_interval.loc['filename'] = filename
        rr_interval.loc['name'] = filename.split('-')[-1]
        # append average and std
        rr_interval.loc['average'] = rr_interval_numpy.mean()
        rr_interval.loc['std'] = rr_interval_numpy.std()

        ret_df = ret_df.append(rr_interval.T, ignore_index=True)

        non_rawvals = ['filename', 'name', 'average', 'std']
        ret_df = ret_df[non_rawvals + [i for i in range(len(ret_df.columns.tolist()) - len(non_rawvals))]]

        return ret_df

    def extract_loop(search_word, all_df):
        """
        :param search_word: str, searching word
        :param all_df: pd.DataFrame
        :return:
        """
        # parse import file
        impact_time_df = pd.read_excel(import_file)
        indices = impact_time_df.index[impact_time_df['filename'].str.contains(search_word)]

        df05, df15, df30, df60 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        for index in indices:
            row_series = impact_time_df.loc[index]
            filename = row_series['filename']
            try:
                path = os.path.join(input_rr_interval_dirpath, filename + '.xlsx')
                data_rr_interval_df = pd.read_excel(path)
            except FileNotFoundError:
                continue
            path = os.path.join(input_hr_dirpath, filename + '-converted.xlsx')
            data_hr_df = pd.read_excel(path)

            # 0.5m
            df05 = extractor(str(row_series['0.5m time']), filename, data_rr_interval_df, data_hr_df, df05)

            # 1.5m
            df15 = extractor(str(row_series['1.5m time']), filename, data_rr_interval_df, data_hr_df, df15)

            # 3.0m
            df30 = extractor(str(row_series['3.0m time']), filename, data_rr_interval_df, data_hr_df, df30)

            # 6.0m
            df60 = extractor(str(row_series['6.0m time']), filename, data_rr_interval_df, data_hr_df, df60)

        df05.to_excel(os.path.join(output_dirpath, search_word + '-05-rr_interval.xlsx'), index=False)
        df15.to_excel(os.path.join(output_dirpath, search_word + '-15-rr_interval.xlsx'), index=False)
        df30.to_excel(os.path.join(output_dirpath, search_word + '-30-rr_interval.xlsx'), index=False)
        df60.to_excel(os.path.join(output_dirpath, search_word + '-60-rr_interval.xlsx'), index=False)

        def _append_info(df, dist):
            df['kind'] = search_word
            df['distance'] = dist
            return all_df.append(df, ignore_index=True)
        all_df = _append_info(df05, 0.5)
        all_df = _append_info(df15, 1.5)
        all_df = _append_info(df30, 3.0)
        all_df = _append_info(df60, 6.0)

        return all_df

    all_df = pd.DataFrame()

    all_df = extract_loop('nov', all_df)
    all_df = extract_loop('pro', all_df)

    # reorder columns
    columns = all_df.columns.tolist()
    non_rawvals = ['filename', 'name', 'average', 'std', 'kind', 'distance']
    all_df = all_df[non_rawvals + [i for i in range(len(columns) - len(non_rawvals))]]
    all_df.to_excel(os.path.join(output_dirpath, 'all.xlsx'), index=False)

    return


if __name__ == '__main__':
    extract_impact()