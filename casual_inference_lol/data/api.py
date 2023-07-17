from urllib.parse import quote
from datetime import datetime
from copy import copy
from typing import List, Dict, Optional, Any
import os
import requests
import json
import time
from dotenv import load_dotenv


class RiotAPI:
    def __init__(
        self,
        small_cycle_interval: int = 1,
        big_cycle_interval: int = 120,
        small_cycle_requests: int = 20,
        big_cycle_requests: int = 100,
    ):
        load_dotenv()
        self._domain = 'api.riotgames.com'
        self._api_key = os.getenv('RIOT_API_KEY')
        if self._api_key is None:
            raise ValueError('The environment variable RIOT_API_KEY does not exist')
        self._small_cycle_interval = small_cycle_interval
        self._big_cycle_interval = big_cycle_interval
        self._small_cycle_requests = small_cycle_requests
        self._big_cycle_requests = big_cycle_requests
        self._first_small_cycle_request_ts: datetime = None
        self._first_big_cycle_request_ts: datetime = None
        self._n_request_small_cycle = 0
        self._n_request_big_cycle = 0

    def _check_cycles(self, verbose: bool = False) -> None:
        ts = datetime.now()
        if (self._first_small_cycle_request_ts is None) and (
            self._first_big_cycle_request_ts is None
        ):
            self._first_small_cycle_request_ts = copy(ts)
            self._n_request_small_cycle = 0
            self._first_big_cycle_request_ts = copy(ts)
            self._n_request_big_cycle = 0

        small_cycle_diff = (
            datetime.now() - self._first_small_cycle_request_ts
        ).total_seconds()
        big_cycle_diff = (
            datetime.now() - self._first_big_cycle_request_ts
        ).total_seconds()

        if small_cycle_diff >= self._small_cycle_interval:
            self._n_request_small_cycle = 0
            self._first_small_cycle_request_ts = copy(ts)

        if big_cycle_diff >= self._big_cycle_interval:
            self._n_request_big_cycle = 0
            self._first_big_cycle_request_ts = copy(ts)
        if verbose:
            print()
            print('=' * 50)
            print(
                f'Requests in {self._small_cycle_interval} seconds: {self._n_request_small_cycle}/{self._small_cycle_requests}'
            )
            print(
                f'Requests in {self._big_cycle_interval} seconds: {self._n_request_big_cycle}/{self._big_cycle_requests}'
            )
            print('=' * 50)

    def _can_make_request(self) -> bool:
        self._check_cycles()
        return (self._n_request_small_cycle < self._small_cycle_requests) and (
            self._n_request_big_cycle < self._big_cycle_requests
        )

    def get(self, region: str, route: str, verbose=True):
        seconds = 0
        while not self._can_make_request():
            time.sleep(1)
            seconds += 1
            print(f'Waiting time: {seconds}s')
        if '?' in route:
            api_route = (
                f'https://{region}.{self._domain}/{route}&api_key={self._api_key}'
            )
        else:
            api_route = (
                f'https://{region}.{self._domain}/{route}?api_key={self._api_key}'
            )
        response = requests.get(api_route)
        self._n_request_small_cycle += 1
        self._n_request_big_cycle += 1
        self._check_cycles(verbose=verbose)
        if response.status_code == 200:
            return json.loads(response.content.decode())
        else:
            raise ValueError(
                f'Error to run {api_route}, the api return the following status code: {response.status_code}'
            )

    def user_info(self, username: str, verbose: bool = False) -> Dict[str, Any]:
        encoded_username = quote(username)
        route = f'lol/summoner/v4/summoners/by-name/{encoded_username}'
        return self.get('br1', route, verbose=verbose)

    def user_matches_ids(
        self,
        puuid: Optional[str] = None,
        username: Optional[str] = None,
        start: int = 0,
        count: int = 20,
        verbose: bool = True,
    ) -> List[str]:
        if puuid is None:
            if username is None:
                raise ValueError('If puuid is null, username is required')
            user_info = self.user_info(username, verbose=verbose)
            puuid = user_info['puuid']
        route = f'lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start={start}&count={count}'
        return self.get('americas', route, verbose=verbose)

    def match_stats(self, match_id, verbose: bool = True):
        route = f'lol/match/v5/matches/{match_id}'
        return self.get('americas', route, verbose=verbose)

    def load_matches(
        self, username, start=0, count=20, sleep_time=30, verbose: bool = True
    ):
        matches_ids = self.user_matches_ids(
            username=username, start=start, count=count, verbose=verbose
        )
        n_matches = len(matches_ids)
        matches_infos = []
        for i, match_id in enumerate(matches_ids):
            if (i + 1) % 10 == 0:
                time.sleep(sleep_time)
            matches_infos.append(self.match_stats(match_id, verbose=verbose))
            print(f'\rMatches loaded: {i + 1}/{n_matches}', end='')
        print()
        return matches_infos
