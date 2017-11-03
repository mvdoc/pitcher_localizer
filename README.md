# Dynamic Face/Body/Scene localizer

This repository contains a PsychoPy implementation of a dynamic localizer, 
 facet inspired from the paradigm by Pitcher, D., Dilks, D. D., Saxe, R. R., 
Triantafyllou, C., & Kanwisher, N. (2011). Differential selectivity for dynamic 
versus static information in face-selective cortical regions. 
*Neuroimage*, 56(4), 2356-2363.

## Details
Each run contains five categories

1. faces
2. objects
3. bodies
4. scenes
5. scrambled objects

which are presented with the following paradigm:

- fixation (18s)
- randomized blocks of categories with no inter-trial interval (18s * 5)
- fixation (18s)
- reversed order of categories as in previous block (18s * 5)
- fixation (18s)

Each block contains six video clips of about 3s each.
Each run lasts 234s.

Participants perform a 1-back repetition detection on the clip. In each run 
there is one such repetition once for every category. By default four runs 
are generated.

### Stimuli
The stimuli are not shared with this repository because I don't have the 
license to release them. Please contact the authors of the original paper, 
or use your own clips. Simply store them in the `stimuli` directory, with a 
subdirectory for each category, e.g.

```
stimuli
├── bodies
├── faces
├── objects
├── scenes
└── scrambled_objects


```

## How To
Running the script without arguments will start a dialog where you can input
the participant's information. Alternatively the script can be run from the
command line with the following arguments
  
```bash
$ python run_localizer.py -h

usage: run_localizer.py [-h] [--subject SUBJECT] [--runnr {1,2,3,4}]
                        [--no-scanner] [--no-fullscreen]

Presentation script for a face/object/scene/bodies localizer, inspired by the
paradigm in Pitcher, D., Dilks, D. D., Saxe, R. R., Triantafyllou, C., &
Kanwisher, N. (2011). Differential selectivity for dynamic versus static
information in face-selective cortical regions. Neuroimage, 56(4), 2356-2363.

optional arguments:
  -h, --help            show this help message and exit
  --subject SUBJECT, -s SUBJECT
                        subject id
  --runnr {1,2,3,4}, -r {1,2,3,4}
                        run nr
  --no-scanner          do not listen to the serial port
  --no-fullscreen       do not run in fullscreen

```


### Extracting logs for BIDS `events.tsv` files
The script will create a logfile for each subject and run under 
`res/sub-id/`. The log contains already all the information to create a BIDS
compliant `events.tsv` files. You just need to grep `BIDS`, and that's it. 
For example:

```bash
$ grep BIDS res/test/sub-test_task-localizer_run-1_20171102T142349.txt | awk '{for (i=3; i<NF; i++) printf $i"\t";print $NF}' | head
onset   duration        stim_type       repetition
0.000   18.000  fixation        None    0
18.000  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_obj_17.mp4        0
20.491  0.000   button_press    null    0
21.002  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_flag.mp4  0
24.002  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_digital_mixer.mp4 0
27.003  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_wind_chimes.mp4   0
30.003  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_candle2.mp4       0
33.003  3.000   scrambled_objects       ./stimuli/scrambled_objects/scrambled_inside_piano.mp4  0
36.004  3.000   bodies  ./stimuli/bodies/body_17.mp4    0
```

Note that also button presses are recorded, so that they can be added as 
additional nuisance regressors in the GLM.

## Acknowledgments

Thanks to [Sarah Herald](http://geon.usc.edu/~sarah/) for sharing the 
initial implementation of the localizer in MATLAB/Psychtoolbox.