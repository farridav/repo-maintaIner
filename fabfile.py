import json
import os

import requests
import yaml

from fabric.api import env, lcd, local, task, abort, prompt
from fabric.colors import green, red, magenta, cyan


def populate_env():
    """
    Populate our env with our settings and a list of available repos
    """

    # Load in env vars if found
    if os.path.isfile('env.yml'):
        with open('env.yml') as settings:
            env_settings = yaml.load(settings.read())

            for key, value in env_settings.iteritems():
                setattr(env, key, value)

    # Build up available repos by walking the repos directory
    env.repos = {}
    env.repo_root = os.path.join(os.path.dirname(__file__), 'repos')
    if not os.path.isdir(env.repo_root):
        os.makedirs(env.repo_root)

    for (path, dirs, files) in os.walk(env.repo_root):
        for repo in dirs:
            env.repos[repo] = {'path': os.path.join(path, repo)}
        break

# Ensure we always populate the env
populate_env()


@task
def use(*args):
    """
    Use the given repos (e.g: fab use:nginx,postgresql pr)
    """
    new_repos = {}
    for repo in args:
        if repo in env.repos:
            new_repos[repo] = env.repos[repo]
        else:
            print(red('{} does not exist, ommiting'.format(repo)))

    env.repos = new_repos


@task
def without(*args):
    """
    Omit the given repos (e.g: fab without:postgresql,nodejs setup)
    """
    for repo in args:
        if repo in env.repos:
            del env.repos[repo]
        else:
            print(red('{} does not exist, skipping'.format(repo)))


@task
def setup():
    """
    Clone all the repos for the given organisation
    """

    # First run, setup and env.yml and track the organisation name
    if 'organisation' not in env:
        org = prompt('\nName of the organisation on github?\n')
        local('echo "---\n\norganisation: {}" > env.yml'.format(org))
        env.organisation = org

    response = requests.get(
        'https://api.github.com/orgs/{}/repos'.format(env.organisation))
    github_response = json.loads(response.content)

    for repo in github_response:
        repo_name = repo['ssh_url'].split('/', -1).pop().replace('.git', '')
        if repo_name not in env.repos:
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

    if len(env.repos.keys()) != 1:
        abort(red('Can only be run with one repo'))

    for repo, data in env.repos.iteritems():
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
                print(magenta('\n\tfab use:{} pr:{}'.format(
                    repo, pr['number'])))

            print(
                cyan('\nfab use:{} pr:#pr_number to work on a PR'.format(repo))
            )
            break

        pr = [pr for pr in github_response if pr['number'] == int(pr_num)]

        if len(pr) == 1:
            pr = pr[0]
        else:
            abort(red('PR not found'))

        with lcd(data['path']):
            local('git remote add {} {}'.format(
                pr['user']['login'], pr['head']['repo']['git_url']
            ))
            local('git fetch {}'.format(pr['user']['login']))
            local('git checkout {}'.format(
                pr['head']['label'].replace(':', '/'))
            )


@task
def sh(command):
    """
    Run an arbitrary shell command on the selected repos
    """
    for repo, data in env.repos.iteritems():
        print(green('\n{}'.format(repo)))
        with lcd(data['path']):
            local(command)
