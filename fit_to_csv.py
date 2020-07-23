"""
Setup: pip install -r requirements.txt
Execute: python fit_to_csv.py <dir of .fit files>
"""

import argparse
import csv
import logging
import os

import fitparse
import pytz

UTC = pytz.UTC
CST = pytz.timezone('US/Eastern')


def main(input_directory, output_file):
    logging.info(f"processing {input_directory}")

    files = os.listdir(input_directory)
    files.sort()
    headers = set(['timestamp', 'heart_rate', 'activity_type', 'activity_type_last_timestamp'])
    data = []
    fit_files = [file for file in files if file[-4:].lower() == '.fit']

    for file in fit_files:
        fitfile = fitparse.FitFile(os.path.join(input_directory, file), data_processor=fitparse.StandardUnitsDataProcessor())
        logging.info(f"converting {file}")
        convert_file(fitfile, headers, data)

    write_to_csv(headers, data, output_file)
    logging.info('finished conversions')


def convert_file(fitfile, headers, data):
    messages = fitfile.messages
    last_timestamp = None
    last_activity_type_timestamp = None

    for m in messages:

        if not hasattr(m, 'fields'):
            continue

        fields = m.fields
        mdata = {}

        for field in fields:
            if field.name in headers:
                if field.name == 'timestamp':
                    mdata[field.name] = UTC.localize(field.value).astimezone(CST)
                    last_timestamp = mdata[field.name]
                elif field.name == 'heart_rate':
                    if int(field.value) > 0:
                        mdata[field.name] = field.value
                elif field.name == 'activity_type':
                    mdata[field.name] = field.value

        if 'activity_type' in mdata:
            if 'timestamp' in mdata:
                last_activity_type_timestamp = mdata['timestamp']
            mdata['activity_type_last_timestamp'] = last_activity_type_timestamp

        if 'heart_rate' in mdata:
            if not 'timestamp' in mdata:
                mdata['timestamp'] = last_timestamp

            data.append(mdata)


def write_to_csv(headers, data, output_file):
    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for entry in data:
            writer.writerow([str(entry.get(k, '')) for k in headers])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert .fit files to CSV')
    parser.add_argument('--input-directory', type=str, help='Input directory fit files', default='.')
    parser.add_argument('--output-file', type=str, help='Output .csv file name', default='out.csv')
    parser.add_argument('--log-level', type=str, help='Set the logging level', default='INFO')
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    main(args.input_directory, args.output_file)
