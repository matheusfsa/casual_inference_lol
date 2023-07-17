import json
import os
from itertools import chain

import pandas as pd

from .api import RiotAPI

DICT_FIELDS = ['perks', 'challenges']
TARGET_FIELD = 'win'
INFO_FIELDS = [
    'teamPosition',
    'puuid',
    'individualPosition',
    'lane',
    'championName',
    'championId',
]
IRRELEVANT_FIELDS = [
    'allInPings',
    'assistMePings',
    'baitPings',
    'championTransform',
    'commandPings',
    'dangerPings',
    'enemyMissingPings',
    'enemyMissingPings',
    'getBackPings',
    'holdPings',
    'item0',
    'item1',
    'item2',
    'item3',
    'item4',
    'item5',
    'item6',
    'needVisionPings',
    'onMyWayPings',
    'participantId',
    'profileIcon',
    'pushPings',
    'riotIdName',
    'riotIdTagline',
    'summonerId',
    'summonerName',
    'teamId',
    'visionClearedPings',
]


def process_participant(participant, user_puuid, match_id):
    for field in DICT_FIELDS + IRRELEVANT_FIELDS:
        if field in participant:
            del participant[field]
    participant['match_id'] = match_id
    participant['is_user'] = participant['puuid'] == user_puuid
    return participant


def process_match(match, user_puuid):
    match_id = match['metadata']['matchId']
    participants = map(
        lambda x: process_participant(x, user_puuid, match_id),
        match['info']['participants'],
    )
    return participants


def process_matches_from_json(username):
    user_puuid = RiotAPI().user_info(username)['puuid']
    results_folder = f'results/{username.replace(" ", "_")}'
    if os.path.isdir(results_folder):
        files = os.listdir(results_folder)
        matches = []
        for filename in files:
            with open(os.path.join('results/ACERTOU_MIZERAVI', filename), 'r') as f:
                matches += json.load(f)
        print(f'# Matches: {len(matches)}')
        processed_matches = chain(*map(lambda x: process_match(x, user_puuid), matches))
        processed_df = pd.DataFrame.from_records(processed_matches)
        print(f'Processed df shape: {processed_df.shape}')
        return processed_df
    else:
        raise ValueError('Directory does not exists!')
