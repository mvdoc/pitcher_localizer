"""Make stimulus order for localizer"""
import argparse
from copy import deepcopy
import json
import os
from os.path import join as pjoin
from glob import glob
from random import shuffle, sample

PWD = os.path.relpath(os.path.dirname(os.path.abspath(__file__)))


def get_stimuli(stim_dir='stimuli'):
    """Returns a dictionary containing the stimuli for each category

    Arguments
    ---------
    stim_dir : str
        directory containing subdirectories with individual stimuli; the
        name of the subdirectories will be the category name

    Returns
    -------
    stimuli : dict
        dictionary containing lists of stimuli for each category
    """
    stimuli = dict()
    categories = glob(pjoin(stim_dir, '*'))
    for cat in categories:
        cat_ = os.path.basename(cat)
        stimuli[cat_] = glob(pjoin(cat, '*'))
    return stimuli


def make_trial(stim_type, duration, stim_fn):
    trial = {
        'stim_type': stim_type,
        'duration': duration,
        'stim_fn': stim_fn
    }
    return trial


def create_run(stimuli):
    """Creates a single run according to Pitcher et al., 2011.
    Each run consists of
        - fixation (18s)
        - randomized block of categories
        - fixation (18s)
        - inverted block of categories
        - fixation (18s)

    Arguments
    ---------
    stimuli : dict
        dictionary containing lists of stimuli for each category

    Returns
    -------
    run : list
        each item in the list is a dictionary with the following keys
            - stim_type : stimulus category
            - duration : stimulus duration in s
            - stim_fn : stimulus fn (if available)
    """
    # randomize categories
    categories = sample(stimuli.keys(), len(stimuli))
    phases = ['fixation', categories, 'fixation', categories[::-1], 'fixation']
    # make a copy and shuffle the stimuli
    stimuli_ = deepcopy(stimuli)
    for stim in stimuli_:
        shuffle(stimuli_[stim])
    run = []
    for ph in phases:
        if ph == 'fixation':
            run.append(make_trial('fixation', 18., None))
        else:  # we have stimuli
            for cat in ph:
                # these are the stimuli
                stims = stimuli_[cat]
                # we have 6 stimuli in each block
                for _ in range(6):
                    run.append(make_trial(cat, 3., stims.pop()))
    return run


def create_experiment(stimuli, nruns):
    """Creates an experiment with nruns"""
    experiment = dict()
    for irun in range(nruns):
        experiment[irun] = create_run(stimuli)

    return experiment


def out_fn(subid, nruns):
    template = 'sub-{0}_task-localizer_{1}runs.json'
    return template.format(subid, nruns)


def save_json(obj, fn, overwrite=False):
    if os.path.exists(fn) and not overwrite:
        raise ValueError("{0} exists, not overwriting".format(fn))
    with open(fn, 'wb') as f:
        json.dump(obj, f, indent=True)


def main():
    parsed = parse_args()
    subid = parsed.subid
    nruns = parsed.nruns
    stim_dir = parsed.stimdir
    out_dir = parsed.output
    overwrite = parsed.overwrite

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    stimuli = get_stimuli(stim_dir)
    exp = create_experiment(stimuli, nruns)
    save_json(exp, pjoin(out_dir, out_fn(subid, nruns)), overwrite)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--subid', '-s', type=str,
                        help='subject id',
                        required=True)
    parser.add_argument('--nruns', '-n', type=int,
                        help='number of runs',
                        default=4)
    parser.add_argument('--stimdir', '-d', type=str,
                        help='directory containing stimuli',
                        default=pjoin(PWD, 'stimuli'))
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite existing files?')
    parser.add_argument('--output', '-o', type=str,
                        help='output directory',
                        required=True)
    return parser.parse_args()


if __name__ == '__main__':
    main()
