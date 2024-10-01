# Affinity API Utils

**Speedinvest, 2024**

These scripts simplify interaction with the [Affinity API](https://api-docs.affinity.co/) by providing tools to read and transform data from Affinity's CRM service. The main use case is to extract data for analysis and display in external systems like Google Sheets, Airtable, and PostgreSQL.

For more information about the Affinity API, see the [API documentation](https://api-docs.affinity.co/) and [Developer Portal](https://developer.affinity.co/).

## Table of Contents

1. [Overview](#overview)
2. [Reading from the Affinity API](#reading-from-the-affinity-api)
    * [Authentication](#authentication)
    * [Options and Usage](#options-and-usage)
3. [Transforming Affinity JSON Data into CSV](#transforming-affinity-json-data-into-csv)

## Overview

This repository contains two main scripts:

1. **`get-from-affinity-api.py`:** Simplifies data retrieval from the Affinity API.
2. **`convert-affinity-json-to-csv.py`:** Converts JSON data from Affinity into CSV format for use in spreadsheet or database applications.

## Reading from the Affinity API

### `get-from-affinity-api.py`

This script simplifies the process of requesting data from Affinity's API by:

* Authenticating using the API token provided by Affinity.
* Handling pagination to retrieve all pages of results.
* Retrying requests in case of failures.
* Pausing and retrying if the request rate limit is exceeded.

#### Example Command

To request a summary of all available lists using the [/lists](https://api-docs.affinity.co/#lists) endpoint of the v1 version of the Affinity API, run:

```bash
$ ./get-from-affinity-api.py -a v1 /lists
```

This command prints the results in JSON format to `stdout`:

```
{"id": 12345, "type": 0, "name": "Portfolio company contacts", "public": false, "owner_id": 3733332, "creator_id": 3733332, "list_size": 235}
{"id": 12346, "type": 1, "name": "Startups Deal Flow", "public": true, "owner_id": 3733333, "creator_id": 3733333, "list_size": 8901}
{"id": 224423, "type": 8, "name": "Limited Partners", "public": false, "owner_id": 3733332, "creator_id": 123456, "list_size": 100}
```

### Authentication

The script looks for a file named `project_secrets.py` in the current directory, which contains the secret API token provided by Affinity. The format of `project_secrets.py` should be:

```
# project_secrets.py
AFFINITY_API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

Alternatively, the `--token` option can be used to pass the token directly through the command line (see [Options and Usage](#options-and-usage)).

### Options and Usage
The available options for `get-from-affinity-api.py` are:

```
usage: get-from-affinity-api.py [-h] [-a API_VERSION] [-t TOKEN] [-r RESULTS_KEY] [-o OUTPUT_FILE] [-d] [-D]
                                [--force-retry] [--delete] [--dry-run]
                                path
```

**Key Options:**

* `--token`: Specify the API token if not using `project_secrets.py`.
* `--results-key`: Extract a specific key from the JSON results, e.g., `--results-key companies`.
* `--force-retry`: Handle 401 errors as if they were 429 (rate limit errors).

For a full list of options, run:

```
$ ./get-from-affinity-api.py --help
```

## Transforming Affinity JSON Data into CSV

### `convert-affinity-json-to-csv.py`

This script converts JSON data obtained from the Affinity API version 2 into CSV format. It is designed to work with the standard JSON representations used for persons, companies, and opportunities in the Affinity system.

**Example Command**

Here is an example that reads from the v2 version of the Affinity API and converts the resulting JSON into CSV format:

```
$ ./get-from-affinity-api.py -a v2 /lists/12346/saved-views/23458/list-entries | ./convert-affinity-json-to-csv.py
```

The output will look like:

```
Affinity Row ID,Organization ID,Name,Domain,Domains,Status,Owner,Team,Fund,Description,Initial Investment Date,Link to document
1234567,2345,Startup Inc.,startupdomain.com,startupdomain.com,,"345678, jane.im@ourvcfirm.com",Fintech,Fund I,The automation platform for everything.,2024-01-01T08:00:00Z,https://drive.google.com/drive/folders/abcdefg123456
1234568,2346,AnotherStartup Inc.,anotherstartupdomain.com,anotherstartupdomain.com,,"345679, sandeep.partner@ourvcfirm.com",Growth,Growth Fund 2024,Another automation platform for everything.,2024-02-01T09:00:00Z,https://drive.google.com/drive/folders/bcdefgh234567
```
