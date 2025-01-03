#!/usr/bin/env python3
""" handles the arr api calls and requests """
import sys
from urllib.parse import urlparse

import requests


class ArrAPI:
    """arr api handler class"""

    def __init__(self):
        self.api_url = ""
        self.api_key = ""
        self.endpoint = {
            "Sonarr": ("series", "tvdb", "shows"),
            "Radarr": ("movie", "tmdb", "movies"),
        }

    # queries arr and gets the return from the end point passed to it
    def arr_get(self, arr, endpoint, timeout):
        """sends the get request to the arr endpoint"""
        try:
            parsed_url = urlparse(self.api_url)

            url_host = parsed_url._replace(
                netloc=parsed_url.netloc.split("@")[-1]
            ).netloc

            url_path = parsed_url.path if parsed_url.path is not None else ""

            request_url = f"{parsed_url.scheme}://{url_host}{url_path}"

            if (parsed_url.username is None) or (parsed_url.password is None):
                response = requests.get(
                    f"{request_url}/api/v3/{endpoint}",
                    params={"apikey": self.api_key},
                    timeout=timeout,
                )
            else:
                response = requests.get(
                    f"{request_url}/api/v3/{endpoint}",
                    params={"apikey": self.api_key},
                    timeout=timeout,
                    auth=(parsed_url.username, parsed_url.password),
                )
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectTimeout:
            print(f"{arr}: Connection Timed Out. Check your URL.")
            sys.exit(1)
        except requests.exceptions.ConnectionError as error:
            print(f"{arr}: Connection Error. Check Your URL or server.")
            error = str(error).split("] ")[1].split("'")[0]
            print(f"{arr}: {error}")
            sys.exit(1)
        except requests.exceptions.HTTPError as error:
            if "401" in str(error):
                print(
                    f"{arr} Error: API key incorrect. "
                    "Please double check your key and config file."
                )
                sys.exit(1)
            print(f"{arr} Error:")
            print(f"{arr}: {error}")
            sys.exit(1)

    def get_id(self, arr, search_term, endpoint, term):
        """sends a request to get get necessary ids"""
        response = self.arr_get(arr, endpoint, 10)

        # creates a dict for the term: id
        id_dict = {item[term]: item["id"] for item in response.json()}

        # if it can't find an id for the term error and exit
        if id_dict.get(search_term) is None:
            print(
                f'{arr} Error: No matching {endpoint if (endpoint != "qualityprofile") else "quality profile"} found.'
            )
            sys.exit(1)

        # return the id
        return id_dict.get(search_term)

    def get_list(self, args, arr):
        """sends the get request to the movies/series arr endpoint"""
        response = self.arr_get(arr, f"{self.endpoint[arr][0]}", 10)
        arr_data = {}

        # parsing out the tmdb/tvdb/imdb id's,
        #  monitored status, quality profile id, title, and any tags
        for item in response.json():
            arr_data[item[f"{self.endpoint[arr][1]}Id"]] = [
                item.get("imdbId"),
                item.get("monitored"),
                item.get("qualityProfileId"),
                item.get("title"),
                item.get("tags"),
                item.get("hasFile") if (arr == "Radarr") else None,
                item.get("genres"),
            ]
        arr_ids = list(arr_data.keys())

        # if its monitored, add to arr ids
        if args.mon:
            arr_ids = [key for key, value in arr_data.items() if value[1]]

        # get the current filtered arr_ids that qualify for the specified quality profile
        if args.qualityprofile:
            qp_id = self.get_id(arr, args.qualityprofile, "qualityprofile", "name")
            arr_ids = list(
                filter(
                    lambda arr_data_item: arr_data.get(arr_data_item, [None])[2]
                    is qp_id,
                    arr_ids,
                )
            )

        # same as above, but for tags
        if args.tag:
            tag_id = self.get_id(arr, args.tag, "tag", "label")
            arr_ids = list(
                filter(
                    lambda arr_tag_item: tag_id
                    in arr_data.get(arr_tag_item, [None])[4],
                    arr_ids,
                )
            )
        if arr == "Radarr" and args.missing:
            arr_ids = list(
                filter(
                    lambda arr_data_item: arr_data.get(arr_data_item, [None])[5]
                    == False,
                    arr_ids,
                )
            )
        if args.genre:
            genres = [genre.strip() for genre in args.genre.split(",")]
            arr_ids = list(
                filter(
                    lambda arr_genre_data_item: any(
                        genre in arr_data.get(arr_genre_data_item, [None])[6]
                        for genre in genres
                    ),
                    arr_ids,
                )
            )

        # if imdb id is in arr, add it to the imdb id list
        arr_imdb = [
            value[1][0]
            for value in arr_data.items()
            if value[1][0] is not None and value[0] in arr_ids
        ]

        return arr_ids, arr_imdb, arr_data
