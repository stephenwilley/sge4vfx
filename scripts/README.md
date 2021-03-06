#Scripts as part of SGE4VFX

##Install

First, go through the scripts and change the variables at the top to reflect your database server details, then put the prolog and epilog scripts in place and configure your queues to use them.

##gridsub (bash)

qsub submits jobs to sge, but because SGE doesn't care about the job once it's done, the gridsub command wraps it and allows us to use another mechanism to track the job.  I'm starting with a pretty basic Postgres DB.

###Notes
1. By using this method, it's important to pass all options to SGE by param rather than putting them in the submission script so they can all be parsed.  Also, the script is not too clever so the submission script must be the last parameter.
2. I'm using Postgres rather than MySQL because people who know better than me told me to.  I don't know enough about it to argue.
3. This submits everything with -ckpt relocate_on_suspend.  I don't know if this stops you using other checkpoint mechanism and needs to be looked into further.

Try it with an example submission like this:

    ====== test.sh ======
    #!/bin/sh
    
    sleep ${SGE_TASK_ID}
    echo "Slept"
    =====================

    gridsub -t 1-100 -q farm.q -S /bin/bash -N test_name test.sh

##prolog

You should set this as the prolog script for your various queues.  It updates the start times and both the task running and the job (if it hasn't already been set).

At the moment, it also puts stdout and stderr paths into the job table.  I wasn't sure how best to go about this since I thought it a bit redundant to have stdout and stderr recorded next to every single task, but doing it this way does assume that the log names end with .<TASKNO> - for example:

    /home/blah/testjob.o2456.1 or /blah/blah/test.4

Maybe it's bad to make this assumption but for my purposes I think it's ok.  File an issue if you think it should be changed.

I put this in ${SGE_ROOT}/${SGE_CELL}/scripts but as long as they're visible to renderboxes I guess they can go anywhere really

##epilog

Set this as the epilog script for your various queues.  It updates the end times of the task as well as the number of tasks completed field in the job.  If the number of tasks finished equals the total number of tasks, then it also sets the end time of the job

It also checks whether the worker part left a return code file in /tmp.  If so, it uses this to update the tasks returncode value in the DB then deletes it.  To have your 'worker' part put an appropriate file somewhere, just include:

    # Write return code for epilog script
    echo $? > /tmp/${JOB_ID}-${SGE_TASK_ID}-return

right after the important command.  You could obviously use some more complex logic to determine whether the job was successful.

As with the prolog script, put it somewhere renderboxes can see it

##logged_in.sh

This is a load sensor script that's used to determine whether anyone's logged in.  I plan on writing a small tool that'll force reboots late in the evening so that workstations are picked up for rendering.

##TODO

* Write a python version of the gridsub script
* Move the various settings out into a common file along the lines of the SGE settings.sh
