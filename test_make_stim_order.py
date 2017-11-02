"""Test module for make_stim_order"""
import pytest
from .make_stim_order import get_stimuli, create_run, \
    inject_attention_check, create_experiment


def test_get_stimuli():
    # smoketest
    stimuli = get_stimuli()
    assert len(stimuli) > 0


def test_create_run():
    stimuli = get_stimuli()
    run = create_run(stimuli)
    run2 = create_run(stimuli)
    assert len(run) > 0
    # check we don't touch stimuli
    for category, stim in stimuli.iteritems():
        assert len(stim) > 0, category
    # check we don't get the same runs
    assert run != run2

    fixations = len(list(filter(lambda x: x['stim_type'] == 'fixation', run)))
    assert fixations == 3

    blocks = []
    block = []
    fixations = 0
    for trial in run:
        stim_type = trial['stim_type']
        if stim_type == 'fixation':
            fixations += 1
            if fixations == 2:
                blocks.append(block)
                block = []
        else:
            block.append(trial)
    blocks.append(block)

    def get_stim_type(x):
        return x['stim_type']

    def get_stim_fn(x):
        return x['stim_fn']

    # we should have the blocks in "palindromic order"
    assert map(get_stim_type, blocks[0]) == map(get_stim_type, blocks[1][::-1])
    # but the individual trials should be different (shuffled)
    block0_stimfn = map(get_stim_fn, blocks[0])
    block1_stimfn = map(get_stim_fn, blocks[1])
    assert block0_stimfn != block1_stimfn[::-1]
    # and also check that we have unique stimuli in each block
    assert len(set(block0_stimfn).intersection(block1_stimfn)) == 0
    # but same length
    assert len(block0_stimfn) == len(block1_stimfn)


def test_inject_attention_check():
    stimuli = get_stimuli()
    exp = create_experiment(stimuli, 4)
    #  category across the runs.
    exp_inj = inject_attention_check(exp)
    exp_inj2 = inject_attention_check(exp)
    assert exp != exp_inj
    assert exp_inj != exp_inj2

    check = dict()
    for irun in sorted(exp_inj.keys()):
        check_run = dict()
        run = exp_inj[irun]
        for itrial in range(1, len(run)):
            trial = run[itrial]
            prev_trial = run[itrial - 1]
            if trial['stim_fn'] == prev_trial['stim_fn']:
                cat = trial['stim_type']
                check_run[cat] = check_run.get(cat, 0) + 1
        check[irun] = check_run

    for irun, check_run in check.iteritems():
        assert sum(check_run.itervalues()) == 5, irun
        assert list(check_run.itervalues()) == [1] * 5

    for run in exp_inj.itervalues():
        assert sum(map(lambda x: x.get('repetition', 0), run)) == 5

