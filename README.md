# repo-maintaIner

A Helpful fabric script for maintaining multiple github projects


## Getting setup

First of all, install the project requirements like so:

    virtualenv .venv && . .venv/bin/activate
    pip install -r requirements.txt

If you already have the repositories you need, then make a `repos` folder in
the root, and put them in here, if not, you can run:

    fab setup

And if prompted, enter the github organisation name, this will checkout all of
the repos for this organisation, and tell you how many issues there are.

## Features

All repos are selected by default when using a task, and some tasks require
you to specify a single repo, you will be warned of this when using them.

To see a list of currently avaialble tasks, type `fab -l`
