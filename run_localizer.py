#!/usr/bin/env python
import sys
from psychopy import visual, gui, event, logging
from psychopy import sound, core
import time as ptime
import serial
import os
from os.path import join as pjoin, exists as pexists
import json
import csv
import datetime
import shutil

# add a new level name called bids
# we will use this level to log information that will be saved
# in the _events.tsv file for this run
BIDS = 26
logging.addLevel(BIDS, 'BIDS')


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
STIMDIR = "stimuli"
RESDIR = "res"
if not pexists(RESDIR):
    os.makedirs(RESDIR)

# load config
with open('config.json', 'rb') as f:
    config = json.load(f)

instructions = config['instructions']
subjectlog = pjoin(RESDIR, config['log_subjects'])
lastinfo = load_subjectlog(subjectlog)

# ask info to experimenter
info = {
    'subject_id': lastinfo['subject_id'],
    'run_nr': 1,
    'scanner?': True,
    'fullscr': True,
}
infdlg = gui.DlgFromDict(dictionary=info,
                         title="Movie Presentation",
                         order=['subject_id', 'run_nr', 'scanner?', 'fullscr']
                         )
if not infdlg.OK:
    core.quit()
# save log of subjects
write_subjectlog(subjectlog, info)

run_nr = int(info['run_nr'])
subj = info['subject_id']
fullscr = info['fullscr']

time = core.Clock()
RESDIR = pjoin(RESDIR, subj)
if not pexists(RESDIR):
    os.makedirs(RESDIR)

log_fn = config['log_template'].format(
    subj=subj,
    task_name=config['task_name'],
    runnr=run_nr,
    timestamp=ptime.strftime(time_template),
)
log_fn = pjoin(RESDIR, log_fn)
log_responses = logging.LogFile(log_fn, level=logging.INFO)


def move_halted_log(fn):
    # flush log
    logging.flush()
    shutil.move(fn, fn.replace('.txt', '__halted.txt'))
    # quit
    core.quit()

# set up global key for quitting; if that happens, log will be moved to
# {log_fn}__halted.txt
event.globalKeys.add(key='q',
                     modifiers=['ctrl'],
                     func=move_halted_log,
                     func_args=[log_fn],
                     name='quit experiment gracefully')

# --- LOAD STIMULI ORDER FOR THIS PARTICIPANT ---
stim_json = pjoin('cfg', 'sub-{0}_task-localizer_4runs.json'.format(subj))
with open(stim_json, 'rb') as f:
    stimuli = json.load(f)[str(run_nr)]
# ------------------------

print "Opening screen"
tbegin = time.getTime()
using_scanner = info['scanner?']
# Setting up visual
if using_scanner:
    size = [1280, 1024]
    fullscr = fullscr
else:
    size = [1024, 768]
    fullscr = fullscr
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
            visual.MovieStim3(scrwin, stim_fn, size=(1280, 940), name=stim_fn,
                              noAudio=True)

scrwin.flip()
cross_hair = visual.TextStim(scrwin, text='+', height=31,
                             pos=(0, 0), color='#FFFFFF')


if using_scanner:
    intro_msg = "Waiting for trigger..."
else:
    intro_msg = "Press Enter to start"
intro_msg = instructions + '\n' + intro_msg
intro = visual.TextStim(scrwin, text=intro_msg, height=31)

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
logging.exp("EXPERIMENT STARTING")
timer_exp = core.Clock()
trunbegin = timer_exp.getTime()
# setup bids log
logbids("onset\tduration\tstim_type")
# duration will be filled later
template_bids = '{onset:.3f}\t{duration:.3f}\t{stim_type}\t{stim_fn}'
# and now we just loop through the trials
for trial in stimuli:
    stim_type = trial['stim_type']
    if stim_type == 'fixation':
        logbids(template_bids.format(
            onset=timer_exp.getTime(),
            duration=trial['duration'],
            stim_type=stim_type,
            stim_fn='n/a'))
        cross_hair.draw()
        scrwin.flip()
        core.wait(trial['duration'])
    else:
        stim_fn = trial['stim_fn']
        movie = stimuli_clip[stim_fn]
        # if we have played it already
        tmovie = core.CountdownTimer(trial['duration'])
        logbids(template_bids.format(
            onset=timer_exp.getTime(),
            duration=trial['duration'],
            stim_type=stim_type,
            stim_fn=stim_fn
        ))
        while tmovie.getTime() > 0:
            if movie.status != visual.FINISHED:
                movie.draw()
                scrwin.flip()
            else:
                cross_hair.draw()
                scrwin.flip()
logging.exp("EXPERIMENT FINISHED")
logging.exp("Done in {0:.2f}s".format(timer_exp.getTime()))
logging.flush()
scrwin.close()
core.quit()
