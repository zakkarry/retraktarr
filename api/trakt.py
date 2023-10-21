#!/usr/bin/env python3
import time
import requests
import json
from config import Configuration


class TraktAPI:
    def __init__(self, oauth2_bearer, trakt_api_key, trakt_user):
        self.oauth2_bearer = oauth2_bearer
        self.trakt_api_key = trakt_api_key
        self.user = trakt_user

        self.list = None
        self.json = None
        self.list_len = []
        self.list_privacy = 'public'
        self.list_limit = 1000
        self.traktSession = requests.Session()
        self.trakt_hdr = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.trakt_api_key,
            'Authorization': f'Bearer {self.oauth2_bearer}'
        }

    def refresh_header(self, oauth_token):
        self.trakt_hdr = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.trakt_api_key,
            'Authorization': f'Bearer {oauth_token}'
        }

    def get_list(self, args, media_type):
        try:
            response = self.traktSession.get(
                f"https://api.trakt.tv/users/settings", headers=self.trakt_hdr, timeout=5)
            response.raise_for_status()
            time.sleep(1)
            if response.status_code == 200:
                self.list_limit = response.json().get('limits', {}).get(
                    "list", {}).get('item_count', None)
            response = self.traktSession.get(
                f"https://api.trakt.tv/users/{self.user}/lists/{self.list}/items", headers=self.trakt_hdr, timeout=10)
            response.raise_for_status()
            if response.status_code == requests.codes.OK:
                self.list_len = [
                    item.get("id", {}) for item in response.json() if item.get("id", {})]
                tvdb_ids = [item.get(media_type, {}).get("ids", {}).get("tvdb") for item in response.json(
                ) if item.get(media_type, {}).get("ids", {}).get("tvdb") is not None]
                tmdb_ids = [item.get(media_type, {}).get("ids", {}).get("tmdb") for item in response.json(
                ) if item.get(media_type, {}).get("ids", {}).get("tmdb") is not None]
                imdb_ids = [item.get(media_type, {}).get("ids", {}).get("imdb") for item in response.json(
                ) if item.get(media_type, {}).get("ids", {}).get("imdb") is not None]

                trakt_ids = [item.get("movie", {}).get("ids", {}).get("trakt") for item in response.json(
                ) if item.get("movie", {}).get("ids", {}).get("trakt") is not None]
                for item in response.json():
                    if item.get("show", {}).get("ids", {}).get("trakt") is not None:
                        trakt_ids.append(item.get("show", {}).get(
                            "ids", {}).get("trakt"))
                return response.json(), tvdb_ids, tmdb_ids, imdb_ids, trakt_ids
        except requests.exceptions.ConnectTimeout as error:
            print("Trakt.tv Error: Connection Timed Out. Check your internet.")
            exit(1)
        except requests.exceptions.ConnectionError as error:
            print("Trakt.tv: Connection Error. Check your internet.")
            print(f"{error}")
            exit(1)
        except requests.exceptions.HTTPError as error:
            if '401' in str(error) or '400' in str(error) or '403' in str(error):
                config = Configuration('config.conf')
                if config.conf.get('Trakt', 'oauth2_refresh') and self.oauth2_bearer == self.trakt_hdr.get("Authorization").split(" ")[1]:
                    print(
                        f"Error: You may have a expired oauth token. Attempting an automatic refresh command.")
                    self.refresh_header(config.get_oauth(args, True))
                    time.sleep(1)
                    return self.get_list(args, media_type)
                print(f"Error: You likely have a bad ClientID/Secret or expired/invalid token.\nPlease check your config and attempt the oauth command (-o) again")
                exit(1)
            elif '404' in str(error):
                time.sleep(1)
                return '', [], [], [], []

    def add_to_list(self, args, media_type, arrData, trakt_ids, idtag, trakt_imdb_ids, arr_ids, arr_imdb, all_trakt_ids):
        trakt_del, trakt_add, extra_imdb_ids, extra_ids, filtered_extra_imdb_ids = {
            media_type: []}, {}, [], [], []
        needed_ids = set(arr_ids)
        if not args.cat:

            if len(all_trakt_ids) > 0:
                needed_ids = set(
                    arr_ids) - set(trakt_ids) if not args.wipe else set(arr_ids)
                extra_ids = set(
                    trakt_ids) - set(arr_ids)
                extra_imdb_ids = set(
                    trakt_imdb_ids) - set(arr_imdb)

                for data in self.json:
                    if data["type"] == media_type.rstrip('s'):
                        if data[media_type.rstrip('s')]["ids"].get(idtag) is None:
                            if data[media_type.rstrip('s')]["ids"].get('imdb') in extra_imdb_ids:
                                filtered_extra_imdb_ids.append(
                                    data[media_type.rstrip('s')]["ids"].get('imdb'))
                if len(extra_ids) > 0 and not args.wipe:
                    trakt_del = {
                        media_type: [{"ids": {idtag: item, "imdb": arrData.get(item, [None])[0]}}
                                     if item in trakt_ids
                                     else {"ids": {'imdb':  arrData.get(item, [None])[0]}}
                                     for item in extra_ids]
                    }
                if len(filtered_extra_imdb_ids) > 0 and not args.wipe:
                    if len(extra_ids) == 0:
                        trakt_del = {
                            media_type: [{"ids": {'imdb': item}}
                                         for item in trakt_imdb_ids]
                        }
                    else:
                        for item in filtered_extra_imdb_ids:
                            trakt_del[media_type].append(
                                {"ids": {'imdb': item}})
                if args.wipe:
                    trakt_del = {
                        "shows": [{"ids": {'trakt': item}}
                                  for item in all_trakt_ids],
                        "movies": [{"ids": {'trakt': item}}
                                   for item in all_trakt_ids]
                    }

        if ((len(self.list_len) + len(needed_ids) - len(extra_ids) - len(extra_imdb_ids)) > self.list_limit) or ((args.wipe) and (len(needed_ids) > self.list_limit)):
            print(
                f'Error: Your additions to ({self.list}) exceeds your item limits. You will need Trakt VIP.')
            exit(1)
        trakt_add = {
            media_type: [{"ids": {idtag: item, "imdb": arrData.get(item, [None])[0]}}
                         if arrData.get(item, [None])[0] is not None
                         else {"ids":  {idtag: item}}
                         for item in needed_ids]
        }
        try:
            if (len(extra_ids) > 0 or len(filtered_extra_imdb_ids) > 0) or (args.wipe and (len(all_trakt_ids) > 0)):

                response = self.traktSession.post(
                    f"https://api.trakt.tv/users/{self.user}/lists/{self.list}/items/remove", headers=self.trakt_hdr, data=json.dumps(trakt_del), timeout=20)
                response.raise_for_status()
                if response.status_code == requests.codes.OK or response.status_code == 204:
                    if not args.wipe:
                        print(
                            f'Number of Deleted {media_type.title()}:  {len(extra_ids) + len(filtered_extra_imdb_ids)}')
                    for extra_id in extra_ids:
                        if extra_id in arrData:
                            print(
                                f"        {idtag.upper()}: {arrData.get(extra_id, [None])[3]} - {extra_id}")
                            continue
                        else:
                            for data in self.json:
                                if data[media_type.rstrip('s')]["ids"][idtag] == extra_id:
                                    print(
                                        f"        {idtag.upper()}: {data[media_type.rstrip('s')]['title']} - {extra_id}")
                                    continue
                    for item in filtered_extra_imdb_ids:
                        for value in arrData.items():
                            if (item == value[1][0]):
                                print(
                                    f"        IMDB: {value[1][3]} - {value[1][0]}")
                                continue

                else:
                    print(
                        f'Failed to delete {media_type.title()}: {len(extra_ids) + len(filtered_extra_imdb_ids)}')
                    exit(1)
            response = self.traktSession.post(
                f"https://api.trakt.tv/users/{self.user}/lists/{self.list}/items", headers=self.trakt_hdr, data=json.dumps(trakt_add), timeout=20)
            response.raise_for_status()
            if response.status_code == 201:
                added_items = response.json()['added'][media_type.lower()]
                listed_items = response.json()['list']['item_count']
                not_found_items = response.json()['not_found'].get(
                    media_type.lower(), [])
                real_not_found_items = []
                for not_found_item in not_found_items:
                    idtag_value = not_found_item.get('ids', {}).get(
                        idtag) if idtag not in not_found_item else not_found_item.get(idtag)
                    if idtag_value is not None and arrData.get(idtag_value, [None])[0] is None:
                        real_not_found_items.append(idtag_value)
                print(f"Number of {media_type.title()} Added: {added_items}")
                if len(real_not_found_items) > 0:
                    print(
                        f"Number of {media_type.title()} Not Found: {len(real_not_found_items)}")
                    for real_not_found_item in real_not_found_items:
                        print(
                            f"        {idtag.upper()}: {arrData.get(real_not_found_item, [None])[3]} - {real_not_found_item}")
                else:
                    print(f"Number of {media_type.title()} Not Found: 0")
                print(f"Number of {media_type.title()} Listed: {listed_items}")
        except requests.exceptions.ConnectTimeout as error:
            print("Trakt.tv Error: Connection Timed Out. Check your internet.")
            exit(1)
        except requests.exceptions.ConnectionError as error:
            print("Trakt.tv: Connection Error. Check your internet.")
            print(f"{error}")
            exit(1)
        except requests.exceptions.HTTPError as error:
            if '401' in str(error) or '403' in str(error):
                print(f"Trakt.tv Error: You likely have a bad OAuth2 Token or ClientID/API key. Please revalidate with the oauth2 script, check your config and try again.")
                exit(1)
            elif '420' in str(error):
                print(
                    f'Trakt.tv Error: Your additions to ({self.trakt_list}) exceeds your item limits. You will need Trakt VIP.')
                exit(1)
            elif '404' in str(error):
                print(
                    f"Trakt.tv Error (404): https://trakt.tv/users/{self.user}/lists/{self.list} not found...")
                print(
                    f"Creating {self.list_privacy} trakt.tv list: ({self.list})...\n")
                trakt_add_list = {
                    'name': self.list,
                    'description': 'This list was create using reTraktarr (https://github.com/zakkarry/reTraktarr)',
                    'privacy': self.list_privacy,
                    'allow_comments': False
                }
                time.sleep(1)
                try:
                    response = self.traktSession.post(
                        f"https://api.trakt.tv/users/{self.user}/lists", headers=self.trakt_hdr, data=json.dumps(trakt_add_list), timeout=10)
                    response.raise_for_status()
                except requests.exceptions.ConnectTimeout as error:
                    print("Trakt.tv Error: Connection Timed Out. Check your internet.")
                    exit(1)
                except requests.exceptions.ConnectionError as error:
                    print("Trakt.tv Error: Connection Problem. Check your internet.")
                    print(f"{error}")
                    exit(1)
                except requests.exceptions.HTTPError as error:
                    print(f"Trakt.tv Error: HTTP exception occurred adding list")
                    print(f"{error}")
                    print(
                        "Further Information: https://trakt.docs.apiary.io/#introduction/status-codes")
                    exit(1)
                try:
                    time.sleep(1)
                    response = self.traktSession.post(
                        f"https://api.trakt.tv/users/{self.user}/lists/{self.list}/items", headers=self.trakt_hdr, data=json.dumps(trakt_add), timeout=20)
                    response.raise_for_status()
                    if response.status_code == 201:
                        added_items = response.json(
                        )['added'][media_type.lower()]
                        listed_items = response.json()['list']['item_count']
                        not_found_items = response.json()['not_found'].get(
                            media_type.lower(), [])
                        real_not_found_items = []
                        for not_found_item in not_found_items:
                            idtag_value = not_found_item.get('ids', {}).get(
                                idtag) if idtag not in not_found_item else not_found_item.get(idtag)
                            if idtag_value is not None and arrData.get(idtag_value, [None])[0] is None:
                                real_not_found_items.append(idtag_value)
                        print(
                            f"Number of {media_type.title()} Added: {added_items}")
                        if len(real_not_found_items) > 0:
                            print(
                                f"Number of {media_type.title()} Not Found: {len(real_not_found_items)}")
                            for real_not_found_item in real_not_found_items:
                                print(
                                    f"        {idtag.upper()}: {arrData.get(real_not_found_item, [None])[3]} - {real_not_found_item}")
                        else:
                            print(
                                f"Number of {media_type.title()} Not Found: 0")
                        print(
                            f"Number of {media_type.title()} Listed: {listed_items}")
                except requests.exceptions.ConnectTimeout as error:
                    print("Trakt.tv Error: Connection Timed Out. Check your internet.")
                    exit(1)
                except requests.exceptions.ConnectionError as error:
                    print("Trakt.tv Error: Connection Problem. Check your internet.")
                    print(f"{error}")
                    exit(1)
                except requests.exceptions.HTTPError as error:
                    if '420' in str(error):
                        print(
                            f'Error: Your list ({self.list}) exceeds your item limits. You will need Trakt VIP.')
                        exit(1)
                    print("Trakt.tv Error:")
                    print(f"{error}")
                    print(
                        "Further Information: https://trakt.docs.apiary.io/#introduction/status-codes")
                    exit(1)
        self.traktSession.close()
