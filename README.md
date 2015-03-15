# Repo Maintainer

A Helpful fabric script for maintaining multiple github projects


## Getting setup

First of all, install the project requirements like so:

    virtualenv .venv && . .venv/bin/activate
    pip install -r requirements.txt

Now add an `env.yml` file, this will be where we store your settings, it is
ignored by our `.gitignore`, and it will looks something like this:

    ---

    organisation: <my_org>
    repo_root: /path/to/my/repos
    repo_exclude:
      - <repo_to_exclude>

The only key here that is mandatory is `organisation`, for a full list of
available keys, see the `DEFAULTS` dictionary in `fabfile.py`

If you dont yet have the repositories you need, then run the following command,
and it will set them up for you, and tell you how many issues they have

    fab clone

If you only want to work with particular repos, you can with the `with` or
`without` task here, examples:

    # Clone only nginx and postgresql
    fab with:nginx,postgresql clone

    # Fetch and purge from the default upstream on everything but nodejs
    fab without:nodejs sh:'git fetch -p'

    # List off all the pull requests within the apt repo
    fab with:apt pr

    # Find PR number 54, add a new remote if necessary, and checkout the branch
    fab with:apt pr:54

## Notes

All repos are selected by default when using a task, and some tasks require
you to specify a single repo, you will be warned of this when using them.

To see a list of currently available tasks, type `fab -l`
