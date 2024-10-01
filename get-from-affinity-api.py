#!/bin/python3

import sys # for stderr and exit
import requests
from time import sleep
import json

import project_secrets

class AffinityClient:
    # supports authentication, pagination,
    # and backoff in case of exceeding rate limits
    def __init__(self, access_token, version='v1'):
        self._access_token = access_token
        if version == 'v1':
            self._base_url = 'https://api.affinity.co'
            self._auth = ('',self._access_token)
            self._headers = {}
        elif version == 'v2':
            self._base_url = 'https://api.affinity.co/v2'
            self._auth = None
            self._headers = {'Authorization': 'Bearer ' + self._access_token}
        else:
            raise NameError(f"unrecognized version parameter: {version}")

    def delete(self, path, params={}, debug=False, debug_retry=False):
        url = path if path[:4] == "http" \
            else self._base_url + ('/' if (path[0] != '/' and self._base_url[-1] != '/') else '') + path
        if debug:
            print(f"Sending delete request to {url} with params {params}", file=sys.stderr)
        resp = requests.delete(url, params=params, auth=self._auth,
            headers=self._headers | {'Accept-Encoding': 'gzip,deflate'})
        if resp.status_code == 429: # server enforcing rate limit
            retry_attempt = 0
            while resp.status_code == 429 and retry_attempt <= 5:
                id_param = repr({k:v for k,v in params.items() if k.endswith("_id")})
                if debug or debug_retry:
                    print(f"Exceeded rate limit. Waiting {2**retry_attempt}s to retry {path} {id_param}...",
                        file=sys.stderr)
                sleep(2**retry_attempt) # exponential backoff, between 1 and 64 seconds
                retry_attempt += 1
                resp = requests.delete(url, params=params, auth=self._auth,
                    headers=self._headers | {'Accept-Encoding': 'gzip,deflate'})

        if resp.status_code != 200:
            id_params = repr({k:v for k,v in params.items() if k.endswith("_id")} or '')
            #if debug:
            #    print(f"Error. Response {resp.text}", file=sys.stderr)
            #raise Exception(f"Failed to get {url} {id_params} : {resp.status_code} {resp.text}")
            print(f"Error response {resp.status_code} : '{resp.text}' when fetching {url} {id_params}", file=sys.stderr)
            sys.exit(1)
        #if debug:
        print(f"Response: {resp}", file=sys.stderr)

    def get(self, path, params={}, page_token=None, results_key=None, force_retry=False, debug=False, debug_retry=False):
        url = path if path[:4] == "http" \
            else self._base_url + ('/' if (path[0] != '/' and self._base_url[-1] != '/') else '') + path
        original_params = params.copy()
        if page_token:
            params['page_token'] = page_token
        if debug:
            print(f"Fetching {url} with params {params}", file=sys.stderr)
            #print(f"headers {self._headers}", file=sys.stderr)
        resp = requests.get(url, params=params, auth=self._auth,
            headers=self._headers | {'Accept-Encoding': 'gzip,deflate'})
        if resp.status_code == 429 or (resp.status_code in [401, 503] and force_retry):
            # server enforcing rate limit or we have been instructed to be persistent
            retry_attempt = 0
            while (resp.status_code == 429 or (resp.status_code in [401, 503] and force_retry)) and retry_attempt <= 5:
                id_param = repr({k:v for k,v in params.items() if k.endswith("_id")})
                if debug or debug_retry:
                    print(f"Waiting {2**retry_attempt}s to retry {path} {id_param}...",
                        file=sys.stderr)
                sleep(2**retry_attempt) # exponential backoff, between 1 and 64 seconds
                retry_attempt += 1
                resp = requests.get(url, params=params, auth=self._auth,
                    headers=self._headers | {'Accept-Encoding': 'gzip,deflate'})

        if resp.status_code != 200:
            id_params = repr({k:v for k,v in params.items() if k.endswith("_id")} or '')
            #if debug:
            #    print(f"Error. Response {resp.text}", file=sys.stderr)
            #raise Exception(f"Failed to get {url} {id_params} : {resp.status_code} {resp.text}")
            print(f"Error response {resp.status_code} : '{resp.text}' when fetching {url} {id_params}", file=sys.stderr)
            sys.exit(1)

        if debug:
            print(f"Response: {resp}", file=sys.stderr)
        resp = resp.json()
        if debug:
            print(f"Response parsed as json: {json.dumps(resp)}", file=sys.stderr)
        next_page_token = None
        next_url = None
        if isinstance(resp, dict):
            next_page_token = resp.get('next_page_token', None) # v1
            next_url = resp.get('pagination', {}).get('nextUrl', None) # v2
            if (next_page_token or next_url) and (not results_key):
                # automatically detect the results_key
                top_level_keys = [x for x in resp.keys() if x not in ['next_page_token', 'pagination']]
                if len(top_level_keys) == 1:
                    results_key = top_level_keys[0]

        if results_key: # used in pagination to separate results from next_page_token
            resp = resp.get(results_key, [])
        if isinstance(resp, dict):
            resp = [resp] # this is a single item response, wrap it in an array to work with the yield later
        if debug:
            print(f"Fetched {len(resp)} records from {path}  {repr(params)}", file=sys.stderr)
        for item in resp:
            yield item

        if next_page_token: # v1
            yield from self.get(path, params=original_params,
                page_token=next_page_token, results_key=results_key, force_retry=force_retry, debug=debug, debug_retry=debug_retry)
        if next_url: # v2
            yield from self.get(next_url, results_key=results_key, force_retry=force_retry, debug=debug, debug_retry=debug_retry)

def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--api-version", default="v1", help="[v1 | v2]")
    parser.add_argument("-t", "--token", default="", help="API access token for v1 and v2 API")
    parser.add_argument("-r", "--results-key", default="", help="Key to extract items from JSON response")
    parser.add_argument("-o", "--output-file", default="", help="write output to file instead of stdout")
    parser.add_argument("-d", "--debug", action='store_true', help="Print some debug info to stderr")
    parser.add_argument("-D", "--debug-retry", action='store_true', help="Print some debug info to stderr in case of error 429 rate limit")
    parser.add_argument("--force-retry", action='store_true', help="Retry 401 errors as if they were 429")
    parser.add_argument("--delete", action='store_true', help="Send a DELETE request instead of GET")
    parser.add_argument("--dry-run", action='store_true', help="Do not make the request")
    parser.add_argument("path", help="path to get, can include URL encoded parameters")
    args = vars(parser.parse_args())

    version = args["api_version"]

    token = args["token"] or project_secrets.AFFINITY_API_KEY or None
    if version in ["v1","v2"] and not token:
        raise NameError(f"token required for API {version}")

    client = AffinityClient(token, version=version)

    if args["dry_run"]:
        print(f"dry run: request {args['path']}")
        print(f"         results_key {args['results_key']}")
        return

    if args["delete"]:
        client.delete(args["path"], debug=args["debug"], debug_retry=args["debug_retry"])
        return

    if args["output_file"]:
        with open(args["output_file"], 'w', 1) as f: # note 1 means line buffered
            for item in client.get(args["path"], results_key=args["results_key"], force_retry=args["force_retry"], debug=args["debug"], debug_retry=args["debug_retry"]):
                f.write(json.dumps(item))
                f.flush()
    else:
        for item in client.get(args["path"], results_key=args["results_key"], force_retry=args["force_retry"], debug=args["debug"], debug_retry=args["debug_retry"]):
            print(json.dumps(item), flush=True)

if __name__ == "__main__":
    main()
