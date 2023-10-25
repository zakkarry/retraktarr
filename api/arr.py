#!/usr/bin/env python3
import requests


class ArrAPI:
    def __init__(self):
        self.arrURL = None
        self.APIKey = None
        self.end_points = {
            'Sonarr': ('series', 'tvdb', 'shows'),
            'Radarr': ('movie', 'tmdb', 'movies')
        }

    def arr_get(self, arr, end_point):
        try:
            response = requests.get(
                f"{self.arrURL}/api/v3/{end_point}", params={'apikey': self.APIKey})
            response.raise_for_status()
            if response.status_code == requests.codes.UNAUTHORIZED:
                print(
                    f"{arr} Error: API key incorrect. Please double check your key and config file.")
                exit(1)
            return response
        except requests.exceptions.ConnectTimeout as error:
            print(f"{arr}: Connection Timed Out. Check your URL.")
            exit(1)
        except requests.exceptions.ConnectionError as error:
            print(f"{arr}: Connection Error. Check Your URL or server.")
            error = str(error).split('] ')[1].split("'")[0]
            print(f"{arr}: {error}")
            exit(1)
        except requests.exceptions.HTTPError as error:
            print(f"{arr} Error:")
            print(f"{arr}: {error}")
            exit(1)

    def get_id(self, arr, search_term, endpoint, term):
        # sends a request to get all quality profiles
        response = self.arr_get(arr, endpoint)

        # creates a dict for the term: id
        dict = {item[term]: item['id']
                for item in response.json()}

        # if it can't find an id for the term error and exit
        if dict.get(search_term) is None:
            print(f"{arr} Error: No matching tag found.")
            exit(1)

        # return the id
        return dict.get(search_term)

    def get_list(self, args, arr):
        # sends the get request to the movies/series arr endpoint
        response = self.arr_get(arr, f"{self.end_points[arr][0]}")
        arrData = {}

        # parsing out the tmdb/tvdb/imdb id's,
        #  monitored status, quality profile id, title, and any tags
        for item in response.json():
            arrData[item[f'{self.end_points[arr][1]}Id']] = [item.get('imdbId'), item.get(
                'monitored'), item.get('qualityProfileId'), item.get('title'), item.get('tags')]
        arr_ids = list(arrData.keys())

        # if its monitored, add to arr ids
        if args.mon:
            arr_ids = [key for key in arrData if arrData[key][1]]

        # get the current filtered arr_ids that qualify for the specified quality profile
        if args.qualityprofile:
            qp_id = self.get_id(arr, args.qualityprofile,
                                'qualityprofile', 'name')
            arr_ids = list(filter(lambda item: arrData.get(item, [None])[
                2] is qp_id, arr_ids))

        # same as above, but for tags
        if args.tag:
            tag_id = self.get_id(arr, args.tag,
                                 'tag', 'label')
            arr_ids = list(
                filter(lambda item: tag_id in arrData.get(item, [None])[4], arr_ids))

        # if imdb id is in arr, add it to the imdb id list
        arr_imdb = [value[1][0] for value in arrData.items(
        ) if value[1][0] is not None and value[0] in arr_ids]

        return arr_ids, arr_imdb, arrData
