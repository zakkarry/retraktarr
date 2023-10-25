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
        self.response = None
        self.list_len = []
        self.list_privacy = 'public'
        self.list_limit = 1000
        self.post_timeout = 60
        self.traktSession = requests.Session()
        self.trakt_hdr = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.trakt_api_key,
            'Authorization': f'Bearer {self.oauth2_bearer}'
        }

    # refresh header (used for oauth automatic refresh)
    def refresh_header(self, oauth_token):
        self.trakt_hdr = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.trakt_api_key,
            'Authorization': f'Bearer {oauth_token}'
        }

    # gets json response from the specified path for applicable media_type (show/movie)
    def get_trakt(self, path, args, media_type, timeout):
        time.sleep(1)
        try:
            response = self.traktSession.get(
                f"https://api.trakt.tv/{path}", headers=self.trakt_hdr, timeout=timeout)
            response.raise_for_status()
            if response.status_code != requests.codes.OK:
                if response.status_code == 404:
                    return 404
                print(
                    f"Trakt.tv Error: Unexpected status code return: {response.status_code}.")
                # exit(1)
            else:
                return response
        except requests.exceptions.ConnectTimeout as error:
            print("Trakt.tv Error: Connection Timed Out. Check your internet.")
            exit(1)
        except requests.exceptions.ConnectionError as error:
            print("Trakt.tv: Connection Error. Check your internet.")
            print(f"{error}")
            exit(1)
        except requests.exceptions.HTTPError as error:
            # checks if an oauth_refresh token is available - and if so assume that the token has expired and attempt a refresh automatically
            if '401' in str(error) or '400' in str(error) or '403' in str(error):
                config = Configuration('config.conf')

                # checks the config for the refresh, if exists, update the header and rerun the command and return original intended results
                if config.conf.get('Trakt', 'oauth2_refresh') and self.oauth2_bearer == self.trakt_hdr.get("Authorization").split(" ")[1]:
                    print(
                        f"Error: You may have a expired oauth token. Attempting an automatic refresh command.")

                    # refresh the header with the new auth, update the config file with new tokens
                    self.refresh_header(config.get_oauth(args, True))
                    time.sleep(1)

                    # return the intended original results
                    return self.get_trakt(path, args, media_type, timeout=timeout)

                # no oauth_refresh token is available, error out.
                print(f"Error: You likely have a bad ClientID/Secret or expired/invalid token.\nPlease check your config and attempt the oauth command (-o) again")
                exit(1)

    # gets the specified trakt list and settings (account limits)
    def get_list(self, args, media_type):
        # grabs the users settings and sets the list limits
        response = self.get_trakt(
            "users/settings", args, media_type, timeout=10)
        self.list_limit = response.json().get('limits', {}).get(
            "list", {}).get('item_count', None)

        # sends a get request for the list and all of its items
        response = self.get_trakt(
            f"users/{self.user}/lists/{self.list}/items", args, media_type, timeout=30)

        # returns empty lists if the list does not exist
        if response == 404:
            return '', [], [], [], []

        # sets all of the ids into lists for parsing/adding/logic
        self.list_len = [
            item.get("id", {}) for item in response.json() if item.get("id", {})]

        tvdb_ids = [item.get(media_type, {}).get("ids", {}).get("tvdb") for item in response.json(
        ) if item.get(media_type, {}).get("ids", {}).get("tvdb") is not None]

        tmdb_ids = [item.get(media_type, {}).get("ids", {}).get("tmdb") for item in response.json(
        ) if item.get(media_type, {}).get("ids", {}).get("tmdb") is not None]

        imdb_ids = [item.get(media_type, {}).get("ids", {}).get("imdb") for item in response.json(
        ) if item.get(media_type, {}).get("ids", {}).get("imdb") is not None]

        # makes a list of all trakt ids so we have every single item guarenteed (we use this id for wiping)
        trakt_ids = [item.get("movie", {}).get("ids", {}).get("trakt") for item in response.json(
        ) if item.get("movie", {}).get("ids", {}).get("trakt") is not None]
        for item in response.json():
            if item.get("show", {}).get("ids", {}).get("trakt") is not None:
                trakt_ids.append(item.get("show", {}).get(
                    "ids", {}).get("trakt"))

        # spit out the lists and json to main
        return response.json(), tvdb_ids, tmdb_ids, imdb_ids, trakt_ids

    # sends a post command to trakt
    # post_json is json.dumps'd json, path is the url to append to the user url
    def post_trakt(self, path, post_json, args, media_type, timeout):
        time.sleep(1)
        try:
            response = self.traktSession.post(
                f"https://api.trakt.tv/users/{self.user}/{path}", headers=self.trakt_hdr, data=post_json, timeout=timeout if not args.timeout else self.post_timeout)
            response.raise_for_status()
            if response.status_code == requests.codes.OK or response.status_code == 204 or response.status_code == 201:
                return response
        except requests.exceptions.ConnectTimeout as error:
            print("Trakt.tv Error: Connection Timed Out. Check your internet.")
            exit(1)
        except requests.exceptions.ReadTimeout as error:
            print(
                "Trakt.tv Error: Connection Timed Out Mid-Stream. Increase your --timeout. ")
            exit(1)
        except requests.exceptions.ConnectionError as error:
            print("Trakt.tv: Connection Error. Check your internet.")
            print(f"{error}")
            exit(1)
        except requests.exceptions.HTTPError as error:
            # http error parsing
            if '401' in str(error) or '403' in str(error):
                print(f"Trakt.tv Error: You likely have a bad OAuth2 Token or ClientID/API key. Please revalidate with the oauth2 script, check your config and try again.")
                exit(1)
            elif '420' in str(error):
                print(
                    f'Trakt.tv Error: Your additions to ({self.trakt_list}) exceeds your item limits. You will need Trakt VIP.')
                exit(1)
            elif '404' in str(error):
                # if the list doesn't exist, we create it, and then rerun the same post commands and return the response as if nothing happened :)
                print(
                    f"Trakt.tv Error (404): https://trakt.tv/users/{self.user}/lists/{self.list} not found...\nCreating {self.list_privacy} trakt.tv list: ({self.list})...\n")
                trakt_add_list = {
                    'name': self.list,
                    'description': 'This list was create using reTraktarr (https://github.com/zakkarry/reTraktarr)',
                    'privacy': self.list_privacy,
                    'allow_comments': False
                }
                # adds the list
                self.post_trakt(
                    f"lists", json.dumps(trakt_add_list), args, media_type, timeout=15)
                time.sleep(1)

                # retry the POST and returns the intended original results
                return self.post_trakt(
                    path, post_json, args, media_type, timeout=timeout if not args.timeout else self.post_timeout)

    def add_to_list(self, args, media_type, arrData, trakt_ids, idtag, trakt_imdb_ids, arr_ids, arr_imdb, all_trakt_ids):
        trakt_del, trakt_add, extra_imdb_ids, extra_ids, filtered_extra_imdb_ids, wrong_ids = {
            media_type: []}, {}, [], [], [], []
        needed_ids = set(arr_ids)  # assumes all tvdb/tmdb id's are necessary

        if not args.cat:  # not catenating to the list

            if len(all_trakt_ids) > 0:  # if the trakt list already has contents

                # if we're not wiping the entire list (--wipe)
                if not args.wipe:

                    needed_ids = set(
                        arr_ids) - set(trakt_ids)  # set needed ids to all wanted ids from arr minus whats already on the list

                    extra_ids = set(
                        trakt_ids) - set(arr_ids)  # all items from the list minus what is in arrs - tmdb/tvdb to be removed

                    extra_imdb_ids = set(
                        trakt_imdb_ids) - set(arr_imdb)  # same as above, but specifically imdbids in case tmdb/tvdb is missing from trakt

                    # run through trakt's API json response for the list
                    for data in self.json:

                        # check if the type of media is show/movie and compare to what arr's media is
                        if data["type"] == media_type.rstrip('s'):

                            # see if the idtag (tvdb/tmdb) is missing
                            if data[media_type.rstrip('s')]["ids"].get(idtag) is None:

                                # check if the imdb is present since tmdb/tvdb is not, and see if its extra (needs to be removed)
                                if data[media_type.rstrip('s')]["ids"].get('imdb') in extra_imdb_ids:

                                    # add the imdb id from trakt to a filtered extra's list
                                    filtered_extra_imdb_ids.append(
                                        data[media_type.rstrip('s')]["ids"].get('imdb'))

                    # check if there are extra tmdb/tvdb id's to be removed from trakt, skip if wipe since we'd remove all
                    if len(extra_ids) > 0 and not args.wipe:
                        trakt_del = {
                            media_type: []}

                        # run through extra_ids, checking if the extra_id from trakt doesnt exist in arrs (almost always deleted/outdate trakt info)
                        for item in extra_ids:
                            if (item not in arr_ids):
                                # if it isn't in our arr, append to the delete json in case its extra - we will readd if its on the needed_ids list later.
                                trakt_del[media_type].append(
                                    {"ids": {idtag: item}})

                                # TODO - NEEDS refactoring. there's gotta be a better way to do this.
                                # TODO - figure out how to escape/break the loops to proceed faster?
                                # TODO - maybe treat it like we do arr data in a dict
                                # checks if the tmdb/tvdb is not in the arr's db and ends up determining if the id is wrong and it will be readded
                                if (item not in arrData.keys()):
                                    # run through the json and check if the imdb id from trakt for the incorrect tvdb/tmdb is in arr
                                    for data in self.json:
                                        # if the tvdb/tmdb id is in the arr
                                        if (data[media_type.rstrip('s')]["ids"].get(idtag) == item):
                                            # run through the arr's id dict
                                            for value in arrData.items():
                                                # if the imdb id is correct but tmdb/tvdb is incorrect
                                                if (data[media_type.rstrip('s')]["ids"].get('imdb') == value[1][0]):
                                                    # if the tmdb/tvdb is going to be readded
                                                    if (value[0] in needed_ids):
                                                        # its a wrong id on trakt, and will be readded, so add to wrong ids
                                                        wrong_ids.append(item)
                                                        break

                    # remove the needed wrong ids from extra_ids so they dont delete
                    extra_ids = set(extra_ids) - set(wrong_ids)

                    # takes the filtered extra imdb ids (missing a corresponding tmdb/tvdb from arr on trakt)
                    if len(filtered_extra_imdb_ids) > 0 and not args.wipe:

                        # if there's no extra_ids (tvdb/tmdb), just build the entire json for imdb since it would be empty anyway
                        if len(extra_ids) == 0:
                            trakt_del = {
                                media_type: [{"ids": {'imdb': item}}
                                             for item in filtered_extra_imdb_ids]
                            }
                        # else, run through the filtered id's and append the imdbid's without corresponding tvdb/tmdb in arr for removal
                        else:
                            for item in filtered_extra_imdb_ids:
                                trakt_del[media_type].append(
                                    {"ids": {'imdb': item}})
                # if filtered is less is 0 or wipe, set needed_ids to all and build a json to delete everything (in case of wipe)
                # we wont run delete if the list is empty anyway...
                else:
                    needed_ids = set(arr_ids)
                    trakt_del = {
                        "shows": [{"ids": {'trakt': item}}
                                  for item in all_trakt_ids],
                        "movies": [{"ids": {'trakt': item}}
                                   for item in all_trakt_ids]
                    }

        # does some calculations on what the end list count would be, and compares to your trakt list limits
        if ((len(self.list_len) + len(needed_ids) - len(extra_ids) - len(extra_imdb_ids)) > self.list_limit) or ((args.wipe) and (len(needed_ids) > self.list_limit)):
            print(
                f'Error: Your additions to ({self.list}) exceeds your item limits. You will need Trakt VIP.')
            exit(1)

        # build the add to list json, if imdb is not available just use tmdb/tvdb
        trakt_add = {
            media_type: [{"ids": {idtag: item, "imdb": arrData.get(item, [None])[0]}}
                         if arrData.get(item, [None])[0] is not None
                         else {"ids":  {idtag: item}}
                         for item in needed_ids]
        }

        # checks if there are extra ids to be removed, or the list has items and a wipe was requested
        # since we removed wrong id's this wont be ran if there is nothing but wrong ids....
        if (len(extra_ids) > 0 or len(filtered_extra_imdb_ids) > 0) or (args.wipe and (len(all_trakt_ids) > 0)):

            # sends the remove from list request
            response = self.post_trakt(
                f'lists/{self.list}/items/remove', json.dumps(trakt_del), args, media_type, timeout=60)

            # if not a wipe, display what was deleted...dont flood if wiping :P
            if not args.wipe:
                print(
                    f'Number of Deleted {media_type.title()}:  {len(extra_ids) + len(filtered_extra_imdb_ids)}')

                # iterate through extra ids (tvdb/tmdb) and display the idname, the title, and the id itself
                for extra_id in extra_ids:
                    # uses the arr's json structure to display info
                    if extra_id in arrData:
                        print(
                            f"        {idtag.upper()}: {arrData.get(extra_id, [None])[3]} - {extra_id}")
                        continue
                    else:
                        # if it can't grab the data from arr, in case it was deleted from the arr, it will search trakt's json (slower) for the titles
                        for data in self.json:
                            if data[media_type.rstrip('s')]["ids"][idtag] == extra_id:
                                print(
                                    f"        {idtag.upper()}: {data[media_type.rstrip('s')]['title']} - {extra_id}")
                                break

                # does the same thing as above, but for items with imdb, but missing tvdb/tmdb on trakt
                # loops through filtered extra imdb's copy, removing from original as it finds matches,
                # so it doesnt double display since the data might be in both arr and trakt
                for item in filtered_extra_imdb_ids.copy():
                    for value in arrData.items():
                        if (item == value[1][0]):
                            print(
                                f"        IMDB: {value[1][3]} - {value[1][0]}")
                            filtered_extra_imdb_ids.remove(item)
                            break
                    if (item in filtered_extra_imdb_ids):
                        for data in self.json:
                            imdbid = data[media_type.rstrip(
                                's')]["ids"].get('imdb')
                            if (imdbid == item):
                                print(
                                    f"        IMDB: {data[media_type.rstrip('s')]['title']} - {imdbid}"
                                )
                                break

        # sends the add to list request
        response = self.post_trakt(
            f'lists/{self.list}/items', json.dumps(trakt_add), args, media_type, timeout=60)

        # gets the count for the add results...
        added_items = response.json()['added'][media_type.lower()]
        listed_items = response.json()['list']['item_count']
        not_found_items = response.json()['not_found'].get(
            media_type.lower(), [])

        # sets the state for items that parsing what really wasnt added due to not corresponding ids
        real_not_found_items = []

        # goes through the ids of not found items on the add request
        for not_found_item in not_found_items:
            # grabs the tvdb/tmdb id of the not found item, we can assume it exists since its coming from arr
            idtag_value = not_found_item.get('ids', {}).get(
                idtag)  # if idtag in not_found_item.get('ids', {}) else not_found_item.get('ids', {}).get('imdb')

            # make sure its not a fucked up json response, and check that the response exists.
            # then append the real not found
            if idtag_value is not None and idtag_value in arrData.keys():
                real_not_found_items.append(idtag_value)

        print(f"Number of {media_type.title()} Added: {added_items}")

        # if real not found is over 0, print the results from the arrData
        if len(real_not_found_items) > 0:
            print(
                f"Number of {media_type.title()} Not Found: {len(real_not_found_items)}")
            for real_not_found_item in real_not_found_items:
                print(
                    f"        {idtag.upper()}: {arrData.get(real_not_found_item, [None])[3]} - {real_not_found_item}")

        # if real not found is 0, finish up with display it found everything, and the total number listed now.
        else:
            print(f"Number of {media_type.title()} Not Found: 0")
        print(f"Number of {media_type.title()} Listed: {listed_items}")

        # close the requests session
        self.traktSession.close()
