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

    def get_qp(self, arr, qp):
        response = self.arr_get(arr, "qualityprofile")

        qp_dict = {item['name']: item['id']
                   for item in response.json()}
        if qp_dict.get(qp) is None:
            print(f"{arr} Error: No matching quality profile found.")
            exit(1)

        return qp_dict.get(qp)

    def get_tags(self, arr, tag):
        response = self.arr_get(arr, "tag")

        tag_dict = {item['label']: item['id']
                    for item in response.json()}
        if tag_dict.get(tag) is None:
            print(f"{arr} Error: No matching tag found.")
            exit(1)

        return tag_dict.get(tag)

    def get_list(self, args, arr):
        response = self.arr_get(arr, f"{self.end_points[arr][0]}")
        arrData = {}

        for item in response.json():
            arrData[item[f'{self.end_points[arr][1]}Id']] = [item.get('imdbId'), item.get(
                'monitored'), item.get('qualityProfileId'), item.get('title'), item.get('tags')]
        arr_ids = list(arrData.keys())

        if args.mon:
            arr_ids = [key for key in arrData if arrData[key][1]]
        if args.qualityprofile:
            arr_ids = list(filter(lambda item: arrData.get(item, [None])[
                2] is self.get_qp(arr, args.qualityprofile), arr_ids))
        if args.tag:
            arr_ids = list(filter(lambda item: self.get_tags(
                arr, args.tag) in arrData.get(item, [None])[4], arr_ids))

        arr_imdb = [value[1][0] for value in arrData.items(
        ) if value[1][0] is not None and value[0] in arr_ids]
        return arr_ids, arr_imdb, arrData
