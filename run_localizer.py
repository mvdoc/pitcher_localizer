#!/usr/bin/env python
"""
Presentation script for a face/object/scene/bodies localizer, inspired by
the paradigm in Pitcher, D., Dilks, D. D., Saxe, R. R., Triantafyllou, C.,
& Kanwisher, N. (2011). Differential selectivity for dynamic versus static
information in face-selective cortical regions. Neuroimage, 56(4), 2356-2363.
"""
import argparse
import sys
from psychopy import visual, gui, event, logging
from psychopy import sound, core
import time as ptime
import serial
import os
from os.path import join as pjoin, exists as pexists, abspath, dirname
import json
import csv
import datetime
import shutil
import subprocess as sp

PWD = os.path.dirname(os.path.abspath(__file__))
# add a new level name called bids
# we will use this level to log information that will be saved
# in the _events.tsv file for this run
BIDS = 26
logging.addLevel(BIDS, 'BIDS')


def move_halted_log(fn):
    # flush log
    logging.flush()
    shutil.move(fn, fn.replace('.txt', '__halted.txt'))
    # quit
    core.quit()


def logbids(msg, t=None, obj=None):
    """logbids(message)
    logs a BIDS related message
    """
    logging.root.log(msg, level=BIDS, t=t, obj=obj)


logging.console.setLevel(logging.INFO)  # receive nearly all messages
time_template = '%Y%m%dT%H%M%S'


def write_subjectlog(fn, info):
    fieldnames = ['subject_id', 'run_nr', 'timestamp']
    info_save = {key: info.get(key, '') for key in fieldnames}
    with open(fn, 'ab') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        info_save['timestamp'] = datetime.datetime.now().isoformat()
        writer.writerow(info_save)


def load_subjectlog(fn):
    lastinfo = {
        'subject_id': 'sidXXXXXX',
        'run_nr': 1
    }
    if not pexists(fn):
        with open(fn, 'wb') as f:
            writer = csv.DictWriter(f,
                                    fieldnames=['subject_id',
                                                'run_nr',
                                                'timestamp'],
                                    delimiter='\t')
            writer.writeheader()
    else:
        with open(fn, 'rb') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = [r for r in reader]
            lastinfo = rows[-1]
    return lastinfo

# set up some dirs
HERE = abspath(dirname(__file__))
STIMDIR = pjoin(HERE, "stimuli")
RESDIR = pjoin(HERE, "res")
if not pexists(RESDIR):
    os.makedirs(RESDIR)

# load config
CONFIG_FN = pjoin(HERE, 'config.json')
with open(CONFIG_FN, 'rb') as f:
    config = json.load(f)

instructions = config['instructions']
subjectlog = pjoin(RESDIR, config['log_subjects'])
lastinfo = load_subjectlog(subjectlog)


def main(info):
    # save log of subjects
    write_subjectlog(subjectlog, info)
    run_nr = int(info['run_nr'])
    subj = info['subject_id']
    fullscr = info['fullscr']
    time = core.Clock()
    subj_dir = pjoin(RESDIR, 'sub-' + subj)
    if not pexists(subj_dir):
        os.makedirs(subj_dir)
    log_fn = config['log_template'].format(
        subj=subj,
        task_name=config['task_name'],
        runnr=run_nr,
        timestamp=ptime.strftime(time_template),
    )
    log_fn = pjoin(subj_dir, log_fn)
    log_responses = logging.LogFile(log_fn, level=logging.INFO)
    # set up global key for quitting; if that happens, log will be moved to
    # {log_fn}__halted.txt
    event.globalKeys.add(key='q',
                         modifiers=['ctrl'],
                         func=move_halted_log,
                         func_args=[log_fn],
                         name='quit experiment gracefully')
    # --- LOAD STIMULI ORDER FOR THIS PARTICIPANT ---
    stim_json = pjoin(PWD, 'cfg',
                      'sub-{0}_task-localizer_4runs.json'.format(subj))
    # create stimulus order if not existing
    if not os.path.exists(stim_json):
        logging.warning("Creating stimulus order for {0}".format(subj))
        MAKESTIMPY = pjoin(HERE, 'make_stim_order.py')
        cmd = "python {cmd} --subid {subj} --output {output} " \
              "--nruns 4".format(cmd=MAKESTIMPY, subj=subj,
                                 output=dirname(stim_json))
        logging.warning("Running '{0}'".format(cmd))
        sp.check_call(cmd.split())
    with open(stim_json, 'rb') as f:
        stimuli = json.load(f)[str(run_nr)]
    # ------------------------
    print "Opening screen"
    tbegin = time.getTime()
    using_scanner = info['scanner?']
    # Setting up visual
    size = [1280, 1024]
    scrwin = visual.Window(size=size,
                           allowGUI=False, units='pix',
                           screen=1, rgb=[-1, -1, -1],
                           fullscr=fullscr)
    # load clips
    print "Loading stimuli"
    loading = visual.TextStim(scrwin,
                              text="Loading stimuli...",
                              height=31)
    loading.draw()
    scrwin.flip()
    stimuli_clip = dict()
    for stim in stimuli:
        if stim['stim_type'] != 'fixation':
            stim_fn = stim['stim_fn']
            print("Loading {0}".format(stim_fn))
            stimuli_clip[stim_fn] = \
                visual.MovieStim3(scrwin, pjoin(PWD, stim_fn),
                                  size=(1280, 940),
                                  name=stim_fn,
                                  noAudio=True, loop=True)
    scrwin.flip()
    cross_hair = visual.TextStim(scrwin, text='+', height=31,
                                 pos=(0, 0), color='#FFFFFF')
    if using_scanner:
        intro_msg = "Waiting for trigger..."
    else:
        intro_msg = "Press Enter to start"
    intro_msg = instructions + '\n' + intro_msg
    intro = visual.TextStim(scrwin, text=intro_msg, height=31, wrapWidth=900)
    # Start of experiment
    intro.draw()
    scrwin.flip()
    # open up serial port and wait for first trigger
    if using_scanner:
        ser_port = '/dev/ttyUSB0'
        ser = serial.Serial(ser_port, 115200, timeout=.0001)
        ser.flushInput()
        trigger = ''
        while trigger != '5':
            trigger = ser.read()
    else:
        from psychopy.hardware.emulator import launchScan
        event.waitKeys(keyList=['return'])
        # XXX: set up TR here
        MR_settings = {
            'TR': 1,
            'volumes': 280,
            'sync': '5',
            'skip': 3,
            'sound': False,
        }
        vol = launchScan(scrwin, MR_settings, globalClock=time, mode='Test')

        class FakeSerial(object):
            @staticmethod
            def read():
                k = event.getKeys(['1', '2', '5'])
                return k[-1] if k else ''

        ser = FakeSerial()

    # set up timer for experiment starting from first trigger
    timer_exp = core.Clock()
    trunbegin = timer_exp.getTime()
    # setup bids log
    logbids("onset\tduration\tstim_type\trepetition")
    # duration will be filled later
    template_bids = '{onset:.3f}\t{duration:.3f}\t{stim_type}\t{stim_fn}\t' \
                    '{repetition}'
    # and now we just loop through the trials
    for trial in stimuli:
        stim_type = trial['stim_type']
        stim_fn = trial['stim_fn']
        duration = trial['duration']
        logbids(template_bids.format(
            onset=timer_exp.getTime(),
            duration=duration,
            stim_type=stim_type,
            stim_fn=stim_fn,
            repetition=trial.get('repetition', 0)),
        )
        trial_counter = core.CountdownTimer(duration)
        if stim_type == 'fixation':
            cross_hair.draw()
            scrwin.flip()
            logging.flush()
            while trial_counter.getTime() > 0:
                pass
        else:
            movie = stimuli_clip[stim_fn]
            while trial_counter.getTime() > 0:
                key = ser.read()
                if key in ['1', '2']:
                    logbids(template_bids.format(
                        onset=timer_exp.getTime(),
                        duration=0.,
                        stim_type='button_press',
                        stim_fn=None,
                        repetition=0)
                    )
                if movie.status != visual.FINISHED:
                    movie.draw()
                    scrwin.flip()
                else:
                    cross_hair.draw()
                    scrwin.flip()
    logging.exp("Done in {0:.2f}s".format(timer_exp.getTime()))
    logging.flush()
    scrwin.close()
    core.quit()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--subject', '-s', type=str,
                        help='subject id')
    parser.add_argument('--runnr', '-r', type=int,
                        help='run nr',
                        choices=range(1, 5))
    parser.add_argument('--no-scanner', action='store_false',
                        help='do not listen to the serial port')
    parser.add_argument('--no-fullscreen', action='store_false',
                        help='do not run in fullscreen')
    return parser.parse_args()


if __name__ == '__main__':
    parsed = parse_args()
    # ask info to experimenter if no args passed

    if parsed.subject is None:
        info = {
            'subject_id': lastinfo['subject_id'],
            'run_nr': 1,
            'scanner?': True,
            'fullscr': True,
        }
        infdlg = gui.DlgFromDict(dictionary=info,
                                 title="Movie Presentation",
                                 order=['subject_id', 'run_nr', 'scanner?',
                                        'fullscr']
                                 )
        if not infdlg.OK:
            core.quit()
    else:
        info = {
            'subject_id': parsed.subject,
            'run_nr': parsed.runnr,
            'scanner?': parsed.no_scanner,
            'fullscr': parsed.no_fullscreen,
        }

    main(info)
