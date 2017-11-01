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
    assert map(get_stim_fn, blocks[0]) != map(get_stim_fn, blocks[1][::-1])
