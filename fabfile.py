import json
import os

import requests
import yaml

from fabric.api import env, lcd, local, task, abort
from fabric.colors import green, red, magenta
from fabric.decorators import with_settings


DEFAULTS = {
    'repo_root': os.path.join(os.path.dirname(__file__), 'repos'),
    'repo_exclude': []
}


def get_available_repos(repo_root):
    """
    Build up available repos by walking the repos directory
    """
    available_repos = {}

    for (path, dirs, files) in os.walk(env.repo_root):
        for repo in dirs:
            available_repos[repo] = {'path': os.path.join(path, repo)}
        break

    return available_repos


def configure():
    """
    Populate our env with our settings and a list of available repos
    """

    # defaults
    config = DEFAULTS.copy()

    # Load in env vars if found
    if os.path.isfile('env.yml'):
        with open('env.yml') as settings:
            env_settings = yaml.load(settings.read())
            config.update(env_settings)

    for key, value in config.iteritems():
        setattr(env, key, value)

    # This may be our first time, if so, make our repo root
    if not os.path.isdir(env.repo_root):
        os.makedirs(env.repo_root)

    env.available_repos = get_available_repos(env.repo_root)

    # default our usable repos to all available ones
    env.repos = env.available_repos.keys()

# Ensure we always load in our config
configure()


@task(alias='with')
def use(*args):
    """
    Use the given repos (e.g: fab with:nginx,postgresql pr)
    """
    repos = []
    for repo in args:
        # Check if the given repo exists in our filesystem
        if repo in env.available_repos:
            repos.append(repo)
        else:
            print(red('{} does not exist, ommiting'.format(repo)))

    env.repos = repos


@task
def without(*args):
    """
    Omit the given repos (e.g: fab without:postgresql,nodejs setup)
    """
    repos = env.repos
    for repo in args:
        # Check if the given repo exists in our filesystem
        if repo in env.available_repos:
            repos.remove(repo)
        else:
            print(red('{} does not exist, skipping'.format(repo)))

    env.repos = repos


@task
def clone():
    """
    Clone all the repos for the given organisation
    """

    response = requests.get(
        'https://api.github.com/orgs/{}/repos'.format(env.organisation))
    github_response = json.loads(response.content)

    for repo in github_response:
        repo_name = repo['ssh_url'].split('/', -1).pop().replace('.git', '')

        if (repo_name not in env.available_repos
                and repo_name not in env.repo_exclude):
            with lcd(env.repo_root):
                print(green('\nCloning {}'.format(repo_name)))
                local('git clone {}'.format(repo['ssh_url']))

        if repo['open_issues_count'] > 0:
            print('{} has {} open issues'.format(
                green(repo['name']),
                red(repo['open_issues_count'])
            ))


@task
def pr(pr_num=None):
    """
    List of all pull requests for the given repo, or checkout a PR

    N.B - designed for only one repo at a time
    """

    if len(env.repos) != 1:
        abort(red('Can only be run with one repo'))

    for repo in env.repos:
        response = requests.get(
            'https://api.github.com/repos/{owner}/{repo}/pulls?state=open&'
            'sort=created&direction=asc'.format(
                owner=env.organisation, repo=repo
            )
        )
        github_response = json.loads(response.content)

        if not pr_num:
            for pr in github_response:
                print(green('\nPull request #{} by {}'.format(
                    pr['number'], pr['user']['login']
                )))
                print(green(pr['body']))
                print(magenta('\n\tfab with:{} pr:{}'.format(
                    repo, pr['number'])))

            break

        pr = [pr for pr in github_response if pr['number'] == int(pr_num)]

        if len(pr) == 1:
            pr = pr[0]
        else:
            abort(red('PR not found'))

        with lcd(env.available_repos[repo]['path']):
            local('git remote add {} {}'.format(
                pr['user']['login'], pr['head']['repo']['git_url']
            ))
            local('git fetch {}'.format(pr['user']['login']))
            local('git checkout {}'.format(
                pr['head']['label'].replace(':', '/'))
            )


@task
@with_settings(warn_only=True)
def sh(command):
    """
    Run an arbitrary shell command on the selected repos
    """
    for repo in env.repos:
        print(green('\n{}'.format(repo)))
        with lcd(env.available_repos[repo]['path']):
            local(command)
