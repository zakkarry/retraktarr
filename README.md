# reTraktarr

`reTraktarr` is a "reverse" [Trakt.tv](https://www.trakt.tv) list implementation for [Radarr](https://radarr.video)/[Sonarr](https://sonarr.tv) that creates [Trakt.tv](https://www.trakt.tv) lists for your movies/series using APIs.

## Introduction

`reTraktarr` is a Python script to sync your [Radarr](https://radarr.video)/[Sonarr](https://sonarr.tv) library to a [Trakt.tv](https://www.trakt.tv) lists using the respective APIs.

The original idea stemmed from my wanting to have a list of monitored movies I could share with friends. This was to be the equivalent of a mdblist, but cherry-picked. Providing a more curated list of what **I** believed was worth considering to watch for downloading.

## Uses

The goal was to add the list to [Radarr](https://radarr.video), set up a filter for the list with Exists in Library and On Exclusion List = false, and allow friends to easily keep up to date with my recommended movies through the Discover tab.

This use case was admittedly very narrow, and a few more use cases have emerged since.

- Backing up entire Radarr/Sonarr libraries, including movies/shows you do not already have downloaded. For example, if it's missing in Radarr, PlexTraktSync would not help.
- Restoring your library easily by importing an entire (backed up) list (in the case of migrating OSs or catastrophic failures)
- Giving someone the ability to browse media you have (without giving them access to Plex/Jellyfin/Emby)
- _Possibly more I have not considered..._

## Requirements

- [Python 3](https://www.python.org/downloads/) (including `requests` module)
  - `pip3 install requests`
- [Radarr](https://radarr.video) and/or [Sonarr](https://sonarr.tv)
- A [Trakt.tv](https://www.trakt.tv) account with [API App configured](#trakttv-api-app-setup)

## Arr Support

`reTraktarr` supports both [Radarr](https://radarr.video) and [Sonarr](https://sonarr.tv) in sourcing the media to sync to your lists. You can specify either or both for syncing, as well as filter what should be added with CLI arguments.

`reTraktarr` will need API access to whichever Arr(s) you intend to use.

## [Trakt.tv](https://www.trakt.tv) API App Setup

A [Trakt.tv](https://www.trakt.tv) account with an [API set up](#trakttv-api-app-setup) is obviously necessary.

- 🚨Note: [Trakt.tv](https://www.trakt.tv) lists have limits. You can read their official statement [here](https://twitter.com/trakt/status/1536751362943332352/photo/1)🚨

1. Head to [Trakt.tv API App Setup Page](https://trakt.tv/oauth/applications)
2. Create a new application, you will only **need** to fill `Name` and `RedirectURI`
   - I suggest using `https://google.com` for your redirect URI. We will need to steal a parameter from the redirect to complete the OAuth2 process.
3. After creating the application, click on it and you will see your `Client ID`, `Client Secret`, and an `Authorize` button.
4. Click `Authorize`. Click `Yes`. You will be redirected to Google (or your URI) and in the URL bar you will see `?code=` followed by 64 alphanumeric characters. **Save this for now. This is your OAuth2 Authorization code.**
5. You can now complete the OAuth2 process when you're ready using the `reTraktarr` script.

## Configuring reTraktarr

`reTraktarr` uses a config file, named `config.conf` to get many of its settings. However, some of these can be overridden with the arguments you pass. You can run `python3 retraktarr.py` at any time to see the available options.

To generate the config template, simply run `python3 retraktarr.py` in a directory without a `config.conf` file present.

Open in your favorite text editor and complete the necessary details for your usage.

If you've never run `reTraktarr` before, you will need to leave your `oauth2_token` and `oauth2_refresh` options blank and use the -oauth argument to complete the authorization process and automatically save your tokens. They will be automatically refreshed if a valid refresh token is available upon expiration.

## Usage (CLI)

```shell
usage: retraktarr.py [-h] [-oauth OAUTH] [-radarr] [-sonarr] [-all] [-mon] [-qualityprofile QUALITYPROFILE] [-tag TAG] [-cat] [-list LIST] [-wipe] [-privacy PRIVACY] [-refresh]

Starr App -> Trakt.tv List Backup/Synchronization

options:
  -h, --help            show this help message and exit
  -oauth OAUTH, -o OAUTH
                        Update OAuth2 Bearer Token. Accepts the auth code and requires valid Trakt config settings. (ex: -o CODE_HERE)
  -radarr, -r           Synchronize monitored Radarr movies with Trakt.tv
  -sonarr, -s           Synchronize monitored Sonarr series with Trakt.tv
  -all, -a              Synchronize both Starr apps with Trakt.tv
  -mon, -m              Synchronize only monitored content with Trakt.tv
  -qualityprofile QUALITYPROFILE, -qp QUALITYPROFILE
                        The quality profile you wish to sync to Trakt.tv
  -tag TAG, -t TAG      The arr tag you wish to sync to Trakt.tv
  -cat, -c              Add to the Trakt.tv list without deletion (concatenate/append to list)
  -list LIST, -l LIST   Specifies the Trakt.tv list name. (overrides config file settings)
  -wipe, -w             Erases the associated list and performs a sync (requires -all or -r/s)
  -privacy PRIVACY, -p PRIVACY
                        Specifies the Trakt.tv list privacy settings (private/friends/public - overrides config file settings)
  -refresh              Forces a refresh_token exchange (oauth) and sets the config to a new tokens.
```

## Troubleshooting

- If you are having problems with old entries not being removed, feel free to use the -wipe command in addition, it will delete the entire **contents** of the list **without** deleting the list itself, and resync.
- If you want to sync multiple "filters" (tag, profile, etc) to one list, consider running multiple times with your filter arguments and the additional -cat parameter.
- Privacy can only be set when the list is first created, specifying privacy on an already created list will do nothing.
- Unless a list is specified using `-list` - when you use `-all` or `-r -s` - each Arr will sync to the list specified in the config.conf file.
- Using filtered syncs with `-all` is not recommended, consider chaining multiple runs.
- Syncing an instance will only remove non-syncing media in its associated type. If you have a list with movies and TV added and run a Sonarr sync to it, it will only remove **SHOWS** that are not present in the sync. (excludes usage of -cat)
- If you repeatedly get the same movies reporting deleted, but not deleting, this is almost certainly due to an outdated ID (usually TMDB) being associated with the movie on Trakt. Report it and give them the correct link. If after it's updated it does not fix it, create an issue with details.
- If you're getting timeouts during runs, particularly during `--wipe` or large list processing, use the `--timeout <sec>` command. Default is 30, increase it until you're list is processed completely.

[start a discussion](https://github.com/zakkarry/reTraktarr/discussions/new) or [open an issue](https://github.com/zakkarry/reTraktarr/issues/new)

[support me with a coffee](https://www.buymeacoffee.com/zak.ary)
