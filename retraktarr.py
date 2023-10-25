#!/usr/bin/env python3
import argparse
# import logging
from api.trakt import TraktAPI
from config import Configuration
from api.arr import ArrAPI


def main():
    # logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',filename='retraktarr.log', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
    parser = argparse.ArgumentParser(
        description="Starr App -> Trakt.tv List Backup/Synchronization")
    parser.add_argument('--oauth', '-o', type=str,
                        help="Update OAuth2 Bearer Token. Accepts the auth code and requires valid Trakt config settings (ex: -o CODE_HERE)")
    parser.add_argument('--radarr', '-r', action='store_true',
                        help="Synchronize monitored Radarr movies with Trakt.tv")
    parser.add_argument('--sonarr', '-s', action='store_true',
                        help="Synchronize monitored Sonarr series with Trakt.tv")
    parser.add_argument('--all', '-a', action='store_true',
                        help="Synchronize both Starr apps with Trakt.tv")
    parser.add_argument('--mon', '-m', action='store_true',
                        help="Synchronize only monitored content with Trakt.tv")
    parser.add_argument('--qualityprofile', '-qp', type=str,
                        help='The quality profile you wish to sync to Trakt.tv')
    parser.add_argument('--tag', '-t', type=str,
                        help='The arr tag you wish to sync to Trakt.tv')
    parser.add_argument('--cat', '-c', action='store_true',
                        help='Add to the Trakt.tv list without deletion (concatenate/append to list)')
    parser.add_argument('--list', '-l', type=str,
                        help="Specifies the Trakt.tv list name. (overrides config file settings)")
    parser.add_argument('--wipe', '-w', action='store_true',
                        help="Erases the associated list and performs a sync (requires -all or -r/s)")
    parser.add_argument('--privacy', '-p', type=str,
                        help="Specifies the Trakt.tv list privacy settings (private/friends/public - overrides config file settings)")
    parser.add_argument('--refresh', action='store_true',
                        help='Forces a refresh_token exchange (oauth) and sets the config to a new tokens.')
    parser.add_argument('--timeout', type=str,
                        help='Specifies the timeout in seconds to use for POST commands to Trakt.tv')
    args = parser.parse_args()

    config = Configuration('config.conf')
    if args.oauth:
        config.get_oauth(args)
    if args.refresh:
        config.get_oauth(args)

    oauth2_bearer, trakt_api_key, trakt_user = config.validate_trakt_credentials()
    trakt_api = TraktAPI(oauth2_bearer, trakt_api_key, trakt_user)
    if (args.list):
        trakt_api.list = args.list
    if (args.privacy):
        trakt_api.list_privacy = args.privacy
    if (args.timeout):
        trakt_api.post_timeout = args.timeout
    if args.radarr or args.all or args.sonarr:
        arr_api = ArrAPI()

    if args.radarr or args.all:
        arr_api.arrURL, arr_api.APIKey, trakt_api.list_privacy, trakt_api.list = config.validate_arr_configuration(
            trakt_api, 'Radarr', args)
        trakt_api.json, tvdb_ids, tmdb_ids, imdb_ids, trakt_ids = trakt_api.get_list(args,
                                                                                     arr_api.end_points['Radarr'][0])
        arr_ids, arr_imdb, arrData = arr_api.get_list(args, 'Radarr')
        trakt_api.add_to_list(args, arr_api.end_points['Radarr'][2], arrData,
                              tmdb_ids, arr_api.end_points['Radarr'][1], imdb_ids, arr_ids, arr_imdb, trakt_ids)
        print(f'Total Movies: {len(arr_ids)}\n')

    if args.sonarr or args.all:
        arr_api.arrURL, arr_api.APIKey, trakt_api.list_privacy, trakt_api.list = config.validate_arr_configuration(
            trakt_api, 'Sonarr', args)
        trakt_api.json, tvdb_ids, tmdb_ids, imdb_ids, trakt_ids = trakt_api.get_list(args,
                                                                                     arr_api.end_points['Sonarr'][2].rstrip('s'))

        arr_ids, arr_imdb, arrData = arr_api.get_list(args, 'Sonarr')
        trakt_api.add_to_list(args, arr_api.end_points['Sonarr'][2], arrData,
                              tvdb_ids, arr_api.end_points['Sonarr'][1], imdb_ids, arr_ids, arr_imdb, trakt_ids)
        print(f'Total Series: {len(arr_ids)}')
        exit(1)

    if args.radarr or args.all:
        exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
