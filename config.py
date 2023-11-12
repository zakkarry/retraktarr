#!/usr/bin/env python3
''' validation and config generation - pretty standard shit '''
import sys
import re
import configparser
import os
import requests


class Configuration:
    ''' configuration file class '''

    def __init__(self, config_file):
        self.conf = configparser.ConfigParser()
        if not os.path.exists(config_file):
            print(
                "Error: Configuration file 'config.conf' not found. Creating blank config.")
            try:
                self.conf['Trakt'] = {
                    'client_id': '',
                    'client_secret': '',
                    'username': '',
                    'redirect_uri': '',
                    'oauth2_token': '',
                }
                self.conf['Radarr'] = {
                    'url': '',
                    'api_key': '',
                    'trakt_list': '',
                    'trakt_list_privacy': ''
                }
                self.conf['Sonarr'] = {
                    'url': '',
                    'api_key': '',
                    'trakt_list': '',
                    'trakt_list_privacy': ''
                }
                with open(config_file, 'w', encoding='utf-8') as configfile:
                    self.conf.write(configfile)
                    print(
                        'Please configure for oauth, use the -o=CODE parameter '
                        'and valid config credentials.')
            except configparser.Error as error:
                print('An error occurred:', error)
            sys.exit(1)
        else:
            try:
                self.conf.read('config.conf')
            except configparser.Error as error:
                print(
                    f'Error occurred while reading the configuration file: {error}')
                sys.exit(1)

    def get_oauth(self, args, refresh=False):
        ''' gets the oauth token via refresh or code '''
        try:
            client_id = self.conf.get('Trakt', 'client_id')
            client_secret = self.conf.get('Trakt', 'client_secret')
            redirect_uri = self.conf.get('Trakt', 'redirect_uri')
            if args.oauth:
                authorization_code = args.oauth
            if refresh or args.refresh:
                authorization_code = self.conf.get(
                    'Trakt', 'oauth2_refresh')
                if authorization_code is None:
                    print(
                        'Trakt.tv Error: Exchanging refresh token failed. '
                        'You do not have a valid refresh_token in your config. '
                        'Please use -o instead.')
                    sys.exit(1)
            if ((len(authorization_code) != 64) or
                    (len(client_id) != 64) or (len(client_secret) != 64)):
                print('You need to set and provide a valid code, client_id, and client_secret. '
                      'Please double check, and rerun the oauth command.')
                sys.exit(1)
            if not re.match(r'^(?:https?://)?(?:[-\w.]+)+(?::\d+)?(?:/.*)?$', redirect_uri):
                print(
                    'You need to set the redirect_uri value to match trakt '
                    'and rerun the oauth command.')
                sys.exit(1)
        except configparser.Error as error:
            print(
                f'Error occurred while reading the configuration values: {error}')
            sys.exit(1)

        oauth_request = {
            'code': authorization_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        if args.refresh or refresh:
            oauth_request['grant_type'] = 'refresh_token'
            oauth_request['refresh_token'] = authorization_code
        try:
            response = requests.post(
                'https://api.trakt.tv/oauth/token',
                json=oauth_request,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            print('Authorization Code: ', authorization_code)
            print('Access Token: ', response.json().get('access_token'))
            print('Refresh Token: ', response.json().get('refresh_token'))
            self.conf.set('Trakt', 'oauth2_token',
                          response.json().get('access_token'))
            self.conf.set('Trakt', 'oauth2_refresh',
                          response.json().get('refresh_token'))
            with open('config.conf', 'w', encoding='utf-8') as configfile:
                self.conf.write(configfile)
                print(
                    'Your configuration file was successfully updated '
                    'with your access/refresh token.\n')
            if args.refresh is False and refresh is False:
                sys.exit(1)
            else:
                return response.json().get('access_token')
        except requests.exceptions.RequestException as error:
            print(error)
            print('Check your configuration, make sure they match Trakt.tv exactly')
            print(
                'Further Information: https://trakt.docs.apiary.io/#introduction/status-codes')
            sys.exit(1)

    def validate_trakt_credentials(self):
        ''' validates trakt.tv credentials '''
        try:
            oauth2_bearer = self.conf.get('Trakt', 'oauth2_token')
            trakt_api_key = self.conf.get('Trakt', 'client_id')
            trakt_secret = self.conf.get('Trakt', 'client_secret')
            user = self.conf.get('Trakt', 'username')
        except configparser.Error as error:
            print(
                f'Error occurred while reading the configuration values: {error}')
            sys.exit(1)
        if (len(user) == 0):
            print('Error: Invalid configuration values. '
                  '[Trakt] username should not be empty.')
            sys.exit(1)
        # validate the lengths of all the keys are correct
        if len(oauth2_bearer) != 64 or len(trakt_api_key) != 64 or len(trakt_secret) != 64:
            print(
                'Error: Invalid configuration values. '
                '[Trakt] oauth2_token/client_id/client_secret '
                'should all have lengths of 64 characters.')
            print('Run with -o parameter with accurate username, redirect_uri, '
                  'client_id, and client_secret values set in config.')
            sys.exit(1)
        return oauth2_bearer, trakt_api_key, user, trakt_secret

    def validate_arr_configuration(self, arr_api, trakt_api, arr, args):
        ''' validates the specified arr config '''
        try:
            if not args.list:
                trakt_api.list = None
            if not args.privacy:
                trakt_api.list_privacy = None

            arr_api.api_url = self.conf.get(arr, 'url').rstrip('/')
            arr_api.api_key = self.conf.get(arr, 'api_key')
            trakt_api.list_privacy = self.conf.get(arr, 'trakt_list_privacy') if (
                trakt_api.list_privacy is None) else trakt_api.list_privacy
            trakt_api.list = self.conf.get(arr, 'trakt_list') if (
                trakt_api.list is None) else trakt_api.list
        except configparser.Error as error:
            print(
                f'Error occurred while reading the configuration values: {error}')
            sys.exit(1)
        if not re.match(r'^(?:https?://)?(?:[-\w.]+)+(?::\d+)?(?:/.*)?$', arr_api.api_url):
            print(
                f"Error: Invalid configuration value. [{arr}] 'url' does not match a URL pattern.")
            sys.exit(1)
        if len(arr_api.api_key) != 32:
            print(
                f'Error: Invalid configuration values. '
                f'[{arr}] api_key should have lengths of 32 characters.')
            sys.exit(1)
