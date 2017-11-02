"""Make stimulus order for localizer"""
import argparse
from copy import deepcopy
import json
import os
from os.path import join as pjoin
from glob import glob
import numpy as np
from random import shuffle, sample, random

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


def get_rand_categories(categories, n, count_categories):
    """Returns a random sample of categories. If n > len(categories),
    then all categories are returned plus some random categories. Also, if
    count_categories is passed, the priority goes to those categories with
    min(count_categories), in oder to counterbalance across runs."""
    n_categories = len(categories)
    idx_min_cat = np.where(count_categories == count_categories.min())[0]
    if n <= len(idx_min_cat):
        rand_idx_cat = sample(idx_min_cat, n)
        sample_categories = [categories[i] for i in rand_idx_cat]
        for i in rand_idx_cat:
            count_categories[i] += 1
        return sample_categories, count_categories
    else:
        # first fill with the minimum
        sample_categories = [categories[i] for i in idx_min_cat]
        for i in idx_min_cat:
            count_categories[i] += 1
        n_ = n - len(sample_categories)
        # then fill with multiples of n_
        for _ in range(n_ // n_categories):
            sample_categories += categories
            # add one to all categories
            count_categories += 1
        # finally fill the remainder
        idx_sample_categories_ = sample(range(n_categories), n_ % n_categories)
        for idx in idx_sample_categories_:
            count_categories[idx] += 1
        sample_categories += [categories[idx]
                              for idx in idx_sample_categories_]
        shuffle(sample_categories)
        return sample_categories, count_categories


def inject_attention_check(exp):
    """Inject some repeated trials randomly throughout the experiment.

    Arguments
    ---------
    exp : dict
        the experiment
    nchecks_run : int
        how many checks for each run to inject. Must be even.

    Returns
    -------
    exp_inj : dict
        the experiment with injected trials
    """
    exp_ = deepcopy(exp)
    # first we need to figure out how many categories we have. we assume
    # that all runs have the same categories
    run_idx = sorted(exp_.keys())
    run1 = exp_[run_idx[0]]
    categories = map(lambda x: x['stim_type'], run1)
    categories = np.unique(filter(lambda x: x != 'fixation', categories))
    n_categories = len(categories)
    # we are going to arbitrarily choose a number of repetitions so that
    # they're balanced across the experiment. it ends up by being a total of
    # n_runs "catch trials" for each category
    for run in exp_.itervalues():
        categories_ = categories.copy()
        shuffle(categories_)
        # randomly split in two blocks
        categories_ = [
            categories_[:n_categories//2],
            categories_[n_categories//2:]]
        shuffle(categories_)
        for check_cat, where_to_check in zip(
                categories_,
                (lambda x: 1 < x < len(run)//2, lambda x: x >= len(run)//2)):
            for cat in check_cat:
                idx_ok = np.where(map(lambda x: x['stim_type'] == cat, run))[0]
                idx_ok = sorted(filter(where_to_check, idx_ok))
                # also do not take the first trial because it's at the edge
                # of two trial types
                idx_ok = idx_ok[1:]
                idx_check = sample(idx_ok, 1)[0]
                run[idx_check] = run[idx_check - 1].copy()
                run[idx_check]['repetition'] = 1
    return exp_


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
    # inject attention check?
    exp = inject_attention_check(exp)
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
