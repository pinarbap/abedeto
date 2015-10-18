import os
from request import DataProvider
from beam_stack import BeamForming
from pyrocko import model
from pyrocko import io
from util import create_directory
from request import DataProvider, CakeTiming
import store_creator
import logging

pjoin = os.path.join

logging.basicConfig(level='INFO')
logger = logging.getLogger('run')


def one_or_error(items):
    e = list(items)
    if len(e)>1:
        raise Exception('more than one item in list. Can only handle one')
    else:
        return e[0]

def one_2_list(items):
    if not isinstance(items, list):
        return [items]


def init(args):
    ev = list(model.Event.load_catalog(args.events))
    if len(ev) == 1:
        if args.name:
            name = args.name
        else:
            name = ev[0].name
        create_directory(name, args.force)
        create_directory(name, args.force)
    else:
        if args.name:
            logger.warn("Cannot use defined name if list of events. Will"
                            " use event names instead")
        for i_e, e in enumerate(ev):
            if e.name:
                name = e.name
            else:
                logger.warn("event name is empty. Skipping...")
                continue

            create_directory(name, args.force)
            create_directory(name, args.force)

            model.Event.dump_catalog([e], pjoin(name, 'event.pf'))
            provider = DataProvider()
            tmin = CakeTiming(phase_selection='first(p|P|PP)-40', fallback_time=100.)
            tmax = CakeTiming(phase_selection='first(p|P|PP)+40', fallback_time=600.)
            provider.download(e, timing=(tmin, tmax), prefix=name, dump_config=True)
            logger.info('.'*30)
            logger.info('Prepared project %s for you' % name)

def getagain(args):
    raise Exception('Not implemented')

def beam(args):
    """Uses tmin timing object, without the offset to calculate the beam"""
    event = list(model.Event.load_catalog('event.pf'))
    assert len(event)==1
    event = event[0]
    provider = DataProvider.load(filename='request.yaml')
    for array_id in provider.use:
        directory = pjoin('array_data', array_id)
        traces = io.load(pjoin(directory, 'traces.mseed'))
        stations = model.load_stations(pjoin(directory, 'stations.pf'))
        bf = BeamForming(stations, traces, normalize=args.normalize)
        bf.process(event=event,
                   timing=provider.timings[array_id].timings[0],
                   fn_dump_center=pjoin(directory, 'array_center.pf'),
                   fn_beam=pjoin(directory, 'beam.mseed'),
                   station=array_id)

def propose_stores(args):
    e = list(model.Event.load_catalog('event.pf'))
    e = one_or_error(e)

    provider = DataProvider.load(filename='request.yaml')
    for array_id in provider.use:
        directory = pjoin('array_data', array_id)
        station = model.load_stations(pjoin(directory, 'array_center.pf'))
        station = one_or_error(station)
        store_creator.propose_store(station, e, superdir=args.store_dir,
                                    source_depth_min=args.sdmin,
                                    source_depth_max=args.sdmax,
                                    source_depth_delta=args.sddelta,
                                    sample_rate=args.sample_rate,
                                    force_overwrite=args.force_overwrite)

def process(args):
    raise Exception('Not implemented')



if __name__=='__main__':
    import argparse

    parser = argparse.ArgumentParser('What was the depth, again?', add_help=True)

    group_init = parser.add_argument_group('Initialization')
    group_init.add_argument('--init',
                            action='store_true',
                            default=False,
                            help='create new job')
    group_init.add_argument('--events',
                        help='Event you don\'t know the depth of')
    group_init.add_argument('--name',
                        help='name')
    group_init.add_argument('--force',
                            action='store_true',
                            default=False,
                            help='force overwrite')

    group_getagain = parser.add_argument_group('Re-retrieve the data')
    group_getagain.add_argument('--getagain',
                                help='',
                                default=False,
                                action='store_true')

    group_beam = parser.add_argument_group('Beam Forming')
    group_beam.add_argument('--beam',
                                help='run beamforming',
                                action='store_true')
    group_beam.add_argument('--normalize',
                                help='normlize by standard deviation of trace',
                                action='store_true',
                            default=True)


    group_getagain = parser.add_argument_group('Create stores')
    group_getagain.add_argument('--storify',
                                help='',
                                default=False,
                                action='store_true')
    group_getagain.add_argument('--super-dir',
                                dest='store_dir',
                                help='super directory where to search/create stores',
                                default='stores')
    group_getagain.add_argument('--source-depth-min',
                                dest='sdmin',
                                help='minimum source depth of store [km]. Default 0',
                                default=0.)
    group_getagain.add_argument('--source-depth-max',
                                dest='sdmax',
                                help='minimum source depth of store [km]. Default 15',
                                default=15.)
    group_getagain.add_argument('--source-depth-delta',
                                dest='sddelta',
                                help='delte source depth of store [km]. Default 1',
                                default=1.)
    group_getagain.add_argument('--sampling-rate',
                                dest='sample_rate',
                                help='samppling rate store [Hz]. Default 10',
                                default=10.)
    group_getagain.add_argument('--force-store',
                                dest='force_overwrite',
                                help='overwrite existent stores',
                                action='store_false')

    args = parser.parse_args()

    if args.init:
        init(args)

    if args.storify:
        propose_stores(args)

    if args.beam:
        beam(args)

    # init
    # -download data, store download infos in subdir

    # getagain
    # first modify get options
    # run getagain

    # storify
    # create possible stores

    # process


