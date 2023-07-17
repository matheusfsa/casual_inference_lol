import json
import os

import click

from casual_inference_lol.data import RiotAPI
from casual_inference_lol.data.process_data import process_matches_from_json


@click.group()
def cli():
    pass


@click.command(name='load_matches')
@click.option('--username', '-u', 'username', type=str)
@click.option('--start', '-s', 'start', type=int, default=0)
@click.option('--count', '-c', 'count', type=int, default=50)
def load_matches(
    username: str,
    start: int,
    count: int,
):
    api = RiotAPI()
    matches = api.load_matches(
        username=username, start=start, count=count, verbose=False
    )
    results_folder = f'results/{username.replace(" ", "_")}'
    if not os.path.isdir(results_folder):
        os.makedirs(results_folder)
    filename = f'matches_{start}_{count}.json'
    filepath = os.path.join(results_folder, filename)
    print(f'The results will be saved on the filepath: {filepath}')
    with open(filepath, 'w') as f:
        json.dump(matches, f)


@click.command(name='process')
@click.option('--username', '-u', 'username', type=str)
def process(
    username: str,
):
    df = process_matches_from_json(username)
    results_folder = f'results/{username.replace(" ", "_")}'
    if not os.path.isdir(results_folder):
        os.makedirs(results_folder)
    filename = 'matches.csv'
    filepath = os.path.join(results_folder, filename)
    print(f'The results will be saved on the filepath: {filepath}')
    df.to_csv(filepath, index=False)


cli.add_command(load_matches)
cli.add_command(process)

if __name__ == '__main__':
    cli()
