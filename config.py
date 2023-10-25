#!/usr/bin/env python3
import re
import configparser
import os
import requests

# validation and config generation - pretty standard shit


class Configuration:
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
                with open(config_file, 'w') as configfile:
                    self.conf.write(configfile)
                    print(
                        "Please configure for oauth, use the -o=CODE parameter and valid config credentials.")
            except Exception as error:
                print("An error occurred:", error)
            exit(1)
        else:
            try:
                self.conf.read('config.conf')
            except configparser.Error as error:
                print(
                    f"Error occurred while reading the configuration file: {error}")
                exit(1)

    def get_oauth(self, args, refresh=False):
        try:
            CLIENT_ID = self.conf.get('Trakt', 'client_id')
            CLIENT_SECRET = self.conf.get('Trakt', 'client_secret')
            REDIRECT_URI = self.conf.get('Trakt', 'redirect_uri')
            if args.oauth:
                AUTHORIZATION_CODE = args.oauth
            if refresh or args.refresh:
                AUTHORIZATION_CODE = self.conf.get(
                    'Trakt', 'oauth2_refresh')
                if AUTHORIZATION_CODE is None:
                    print(
                        "Trakt.tv Error: Exchanging refresh token failed. You do not have a valid refresh_token in your config. Please use -o instead.")
                    exit(1)
            if (len(AUTHORIZATION_CODE) != 64) or (len(CLIENT_ID) != 64) or (len(CLIENT_SECRET) != 64):
                print("You need to set and provide a valid code, client_id, and client_secret. Please double check, and rerun the oauth command.")
                exit(1)
            if not re.match(r'^(?:https?://)?(?:[-\w.]+)+(?::\d+)?(?:/.*)?$', REDIRECT_URI):
                print(
                    "You need to set the redirect_uri value to match trakt and rerun the oauth command.")
                exit(1)
        except configparser.Error as error:
            print(
                f"Error occurred while reading the configuration values: {error}")
            exit(1)

        oauth_request = {
            "code": AUTHORIZATION_CODE,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        if args.refresh or refresh:
            oauth_request["grant_type"] = "refresh_token"
            oauth_request["refresh_token"] = AUTHORIZATION_CODE
        try:
            response = requests.post(
                "https://api.trakt.tv/oauth/token",
                json=oauth_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print("Authorization Code: ", AUTHORIZATION_CODE)
            print("Access Token: ", response.json().get("access_token"))
            print("Refresh Token: ", response.json().get("refresh_token"))
            self.conf.set('Trakt', 'oauth2_token',
                          response.json().get("access_token"))
            self.conf.set('Trakt', 'oauth2_refresh',
                          response.json().get("refresh_token"))
            with open('config.conf', 'w') as configfile:
                self.conf.write(configfile)
                print(
                    "Your configuration file was successfully updated with your oauth2 access/refresh token.\n")
            if args.refresh == False and refresh == False:
                exit(1)
            else:
                return response.json().get("access_token")
        except requests.exceptions.RequestException as error:
            print(error)
            print("Check your configuration, make sure they match Trakt.tv exactly")
            print(
                "Further Information: https://trakt.docs.apiary.io/#introduction/status-codes")
            exit(1)

    def validate_trakt_credentials(self):
        try:
            oauth2_bearer = self.conf.get('Trakt', 'oauth2_token')
            trakt_api_key = self.conf.get('Trakt', 'client_id')
            trakt_secret = self.conf.get('Trakt', 'client_secret')
            trakt_user = self.conf.get('Trakt', 'username')
        except configparser.Error as error:
            print(
                f"Error occurred while reading the configuration values: {error}")
            exit(1)

        # validate the lengths of all the keys are correct
        if len(oauth2_bearer) != 64 or len(trakt_api_key) != 64 or len(trakt_secret) != 64:
            print(
                "Error: Invalid configuration values. [Trakt] oauth2_token/client_id/client_secret should all have lengths of 64 characters.")
            print("Run with -o parameter with accurate username, redirect_uri, client_id, and client_secret values set in config.")
            exit(1)
        return oauth2_bearer, trakt_api_key, trakt_user

    def validate_arr_configuration(self, trakt_api, arr, args):
        try:
            if not args.list:
                trakt_api.list = None
            if not args.privacy:
                trakt_api.list_privacy = None

            arrURL = self.conf.get(arr, 'url').rstrip('/')
            arrAPIKey = self.conf.get(arr, 'api_key')
            arr_list_privacy = self.conf.get(arr, 'trakt_list_privacy') if (
                trakt_api.list_privacy is None) else trakt_api.list_privacy
            arrtrakt_list = self.conf.get(arr, 'trakt_list') if (
                trakt_api.list is None) else trakt_api.list
        except configparser.Error as error:
            print(
                f"Error occurred while reading the configuration values: {error}")
            exit(1)
        if not re.match(r'^(?:https?://)?(?:[-\w.]+)+(?::\d+)?(?:/.*)?$', arrURL):
            print(
                f"Error: Invalid configuration value. [{arr}] 'url' does not match a URL pattern.")
            exit(1)
        if len(arrAPIKey) != 32:
            print(
                f'Error: Invalid configuration values. [{arr}] api_key should have lengths of 32 characters.')
            exit(1)
        return arrURL, arrAPIKey, arr_list_privacy, arrtrakt_list
