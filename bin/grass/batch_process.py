#!/usr/bin/env python3

import os
import sys
import argparse

from smoderp2d.runners.grass import GrassGisRunner
from smoderp2d.exceptions import ProviderError, MaxIterationExceeded

def run_process(params, epsg):
    retcode = 0
    runner = None
    try:
        runner = GrassGisRunner()
        runner.create_location(f'EPSG:{epsg}')
        runner.set_options(params)
        runner.import_data()
        runner.run()
    except (ProviderError, MaxIterationExceeded) as e:
        print(f'ERORR: {e}', file=sys.stderr)
        retcode = 1

    if runner is not None:
        runner.finish()

    return retcode

def main(params, epsg):
    sys.exit(run_process(params, epsg))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='batch_process',
        description='Run SMODERP2D as batch process'
    )
    parser.add_argument('--elevation', required=True)
    parser.add_argument('--soil', required=True)
    parser.add_argument('--soil_type_fieldname', required=True)
    parser.add_argument('--vegetation', required=True)
    parser.add_argument('--vegetation_type_fieldname', required=True)
    parser.add_argument('--rainfall_file', required=True)
    parser.add_argument('--end_time', required=True)
    parser.add_argument('--maxdt', required=True)
    parser.add_argument('--table_soil_vegetation', required=True)
    parser.add_argument('--table_soil_vegetation_fieldname', required=True)
    parser.add_argument('--output', required=True)    
    parser.add_argument('--points')
    parser.add_argument('--points_fieldname')
    parser.add_argument('--streams')
    parser.add_argument('--channel_properties_table')
    parser.add_argument('--streams_channel_type_fieldname')
    parser.add_argument('--flow_direction', default='single')
    parser.add_argument('--wave', default='kinematic')
    parser.add_argument('--generate_temporary', action='store_true')
    parser.add_argument('--epsg', default=5514)

    args = parser.parse_args()

    main({
        'elevation': args.elevation,
        'soil': args.soil,
        'soil_type_fieldname': args.soil_type_fieldname,
        'vegetation': args.vegetation,
        'vegetation_type_fieldname': args.vegetation_type_fieldname,
        'rainfall_file': args.rainfall_file,
        'end_time': args.end_time,
        'maxdt': args.maxdt,
        'output': args.output,
        'points': args.points,
        'points_fieldname': args.points_fieldname,
        'streams': args.streams,
        'table_soil_vegetation': args.table_soil_vegetation,
        'table_soil_vegetation_fieldname': args.table_soil_vegetation_fieldname,
        'channel_properties_table': args.channel_properties_table,
        'streams_channel_type_fieldname': args.streams_channel_type_fieldname,
        'flow_direction': args.flow_direction,
        'wave': args.wave,
        'generate_temporary': bool(args.generate_temporary)
    }, epsg=args.epsg
         )
