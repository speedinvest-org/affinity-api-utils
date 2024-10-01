# Affinity API Utils

Speedinvest, 2024

These scripts work with the [Affinity API](https://api-docs.affinity.co/) to simplify reading data from the Affinity CRM service. The primary use case is to enable the data to be displayed and analyzed outside Affinity, in systems such as Google Sheets, Airtable, PostgreSQL, etc.

For more information about the Affinity API, see https://api-docs.affinity.co/ and https://developer.affinity.co/

## Reading from the Affinity API

The script called `get-from-affinity-api.py` simplifies the process of requesting data from Affinity's API by

* authenticating using the token provided by Affinity
* requesting each additional page of results
* retrying in case of failure
* pausing and retring in case of exceeding request rate limit

Here is an example requesting a summary of all of the available lists, using the [/lists](https://api-docs.affinity.co/#lists) endpoint of the v1 version of the Affinity API:
 
```
$ ./get-from-affinity-api.py -a v1 /lists
```

The results are in JSON format, and are printed to stdout:

```
{"id": 12345, "type": 0, "name": "Portfolio company contacts", "public": false, "owner_id": 3733332, "creator_id": 3733332, "list_size": 235}
{"id": 12346, "type": 1, "name": "Startups Deal Flow", "public": true, "owner_id": 3733333, "creator_id": 3733333, "list_size": 8901}
{"id": 224423, "type": 8, "name": "Limited Partners", "public": false, "owner_id": 3733332, "creator_id": 123456, "list_size": 100}
```
### Authentication

The script looks for a file called `project_secrets.py` in the current directory, which can contain the secret API token provided by Affinity in the logged-in user's [/settings/api](https://speedinvest.affinity.co/settings/api) page.

```
$ cat project_secrets
AFFINITY_API_KEY='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### Options and usage

```
usage: get-from-affinity-api.py [-h] [-a API_VERSION] [-t TOKEN] [-r RESULTS_KEY] [-o OUTPUT_FILE] [-d] [-D]
                                [--force-retry] [--delete] [--dry-run]
                                path
```

Notes:

* `--token` is required if the file `project_secrets.py` is not used (see above)
* `--results-key` can be used to pull out/up results from inside the JSON, for example `--results-key companies`
* `--force-retry` handles 401 errors as if they were 429 (rate limit errors)

## Transforming Affinity JSON data into CSV

The Affinity API uses a set of common JSON representations for many of the data it provides. The script called `convert-affinity-json-to-csv.py` transforms Affinity's JSON representation of persons, companies, and opportunities into CSV format. This enables loading the data into systems that work with tabular data such as spreadsheets and relational databases.

Here is an example that reads from the v2 version of the Affinity API that converts the resulting JSON into CSV:

```
$ ./get-from-affinity-api.py -a v2 /lists/12346/saved-views/23458/list-entries | ./convert-affinity-json-to-csv.py
```

The results look like this:

```
Affinity Row ID,Organization ID,Name,Domain,Domains,Status,Owner,Team,Fund,Description,Initial Investment Date,Link to document
1234567,2345,Startup Inc.,startupdomain.com,startupdomain.com,,"345678, jane.im@ourvcfirm.com",Fintech,Fund I,The automation platform for everything.,2024-01-01T08:00:00Z,https://drive.google.com/drive/folders/abcdefg123456
1234568,2346,AnotherStartup Inc.,anotherstartupdomain.com,anotherstartupdomain.com,,"345679, sandeep.partner@ourvcfirm.com",Growth,Growth Fund 2024,Another automation platform for everything.,2024-02-01T09:00:00Z,https://drive.google.com/drive/folders/bcdefgh234567
```

