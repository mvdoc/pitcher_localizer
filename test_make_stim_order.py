"""Test module for make_stim_order"""
import pytest
from .make_stim_order import get_stimuli, create_run


def test_get_stimuli():
    # smoketest
    stimuli = get_stimuli()
    assert len(stimuli) > 0


def test_create_run():
    stimuli = get_stimuli()
    run = create_run(stimuli)
    assert len(run) > 0
    # check we don't touch stimuli
    for category, stim in stimuli.iteritems():
        assert len(stim) > 0, category

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
