import sys, glob, os, argparse
import pandas as pd
import numpy as np
from time import mktime, gmtime
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='Convert hexoskin raw data into hr data.')
parser.add_argument('duration', type=int, default=10, help='Duration time to impact-hr[s]')
parser.add_argument('-i', '--input-dir', type=str, default=os.path.join('hexoskin', 'hr'),
                    help='Input directory path')
parser.add_argument('-o', '--output-dir', type=str, default=os.path.join('hexoskin', 'impact-hr'),
                    help='Output directory path')
parser.add_argument('-f', '--import-file', type=str, default=os.path.join('hexoskin', 'impact-time.xlsx'),
                    help='Import file')

args = parser.parse_args()

def extract_impact():
    duration_time = args.duration
    input_dirpath = args.input_dir
    output_dirpath = args.output_dir
    import_file = args.import_file


    def extractor(column, filename, data_df, ret_df):
        """
        :param column: str, column name if it's None, get rest
        :param filename: str, filename
        :param ret_df: pd.DataFrame, appended extracted data for row
        :return:
        """
        if column:
            # get index
            ind = data_df['time'][data_df['time'] == column].index[0]
        else:
            ind = 50
        # get heart-rate
        hr = data_df.iloc[:, [6]][ind - duration_time + 1:ind + 1]

        # rename index
        rename = {ind: c for c, ind in enumerate(hr.index)}

        # get hr
        hr_numpy = hr.values.squeeze()
        hr = hr.rename(rename, axis='index')

        # append filename and name to first rows
        hr.loc['filename'] = filename
        hr.loc['name'] = filename.split('-')[-1]
        # append average and std
        hr.loc['average'] = hr_numpy.mean()
        hr.loc['std'] = hr_numpy.std()
        hr.loc['max'] = hr_numpy.max()

        ret_df = ret_df.append(hr.T, ignore_index=True)

        non_rawvals = ['filename', 'name', 'average', 'std', 'max']
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

        dfrest, df05, df15, df30, df60 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        for index in indices:
            row_series = impact_time_df.loc[index]
            filename = row_series['filename']
            path = os.path.join(input_dirpath, filename + '-converted.xlsx')
            data_df = pd.read_excel(path)

            # rest
            dfrest = extractor(None, filename, data_df, dfrest)

            # 0.5m
            df05 = extractor(str(row_series['0.5m time']), filename, data_df, df05)

            # 1.5m
            df15 = extractor(str(row_series['1.5m time']), filename, data_df, df15)

            # 3.0m
            df30 = extractor(str(row_series['3.0m time']), filename, data_df, df30)

            # 6.0m
            df60 = extractor(str(row_series['6.0m time']), filename, data_df, df60)

        dfrest.to_excel(os.path.join(output_dirpath, search_word + '-rest-hr.xlsx'), index=False)
        df05.to_excel(os.path.join(output_dirpath, search_word + '-05-hr.xlsx'), index=False)
        df15.to_excel(os.path.join(output_dirpath, search_word + '-15-hr.xlsx'), index=False)
        df30.to_excel(os.path.join(output_dirpath, search_word + '-30-hr.xlsx'), index=False)
        df60.to_excel(os.path.join(output_dirpath, search_word + '-60-hr.xlsx'), index=False)


        def _append_rest(dfs, dfrest):
            for df in dfs:
                df['average(rest)'] = dfrest['average']
                df['std(rest)'] = dfrest['std']
                df['max(rest)'] = dfrest['max']
        #_append_rest([df05, df15, df30, df60], dfrest)

        def _append_info(df, dist):
            df['kind'] = search_word
            df['distance'] = dist
            return all_df.append(df, ignore_index=True)

        all_df = _append_info(dfrest, 'rest')
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
    #non_rawvals = ['filename', 'name', 'average', 'std', 'max', 'kind', 'distance', 'average(rest)', 'std(rest)', 'max(rest)']
    non_rawvals = ['filename', 'name', 'average', 'std', 'max', 'kind', 'distance']
    all_df = all_df[non_rawvals + [i for i in range(len(columns) - len(non_rawvals))]]
    all_df.to_excel(os.path.join(output_dirpath, 'all.xlsx'), index=False)

    return


if __name__ == '__main__':
    extract_impact()