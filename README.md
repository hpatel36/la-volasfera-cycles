# La Volasfera Cycle Explorer

La Volasfera Cycle Explorer is a small Flask web application for examining
True North Node stationary points and converse astrological cycles. It is being
developed as a free companion tool for La Volasfera articles.

## Project status

The Flask and Render foundation and the True Node cycle calculation engine are
in place. The web interface for entering reference and anchor dates is the next
development stage.

## Local development

The project currently uses Python 3.13.6.

```bat
py -3 -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

Open <http://127.0.0.1:5000> in a browser. The health endpoint is available at
<http://127.0.0.1:5000/health>.

Run the tests with:

```bat
python -m pytest
```

## Swiss Ephemeris data

True Node calculations from 1400 through 2100 require the lunar files
`semo_12.se1` and `semo_18.se1`. Binary `.se1` files are deliberately excluded
from Git. Download the exact tested versions with:

```bat
python scripts\download_ephemeris.py
```

The downloader uses an official Swiss Ephemeris GitHub revision and verifies
both files with pinned SHA-256 checksums. Set `SE_EPHE_PATH` to use a different
local directory. Render downloads the files into `./ephe` during its build and
starts the application with strict validation enabled.

For a local strict-startup check in Command Prompt:

```bat
set EPHEMERIS_REQUIRED=true
set SE_EPHE_PATH=ephe
python -m flask --app app run --debug
```

## Calculation engine

`calculations/node_stations.py` calculates True North Node stationary events
from Swiss Ephemeris data at request time. It does not use a deployed database.
The default station selector reproduces the historical AstriumLab event set;
an exhaustive scanner is also available for inspecting every stable speed sign
change, including short-lived pairs outside that compatibility set.

`calculations/cycles.py` supports transit, secondary, tertiary and minor
timelines in both direct and converse directions. A full local regression
generates all 35,002 compatibility events from 1400 through 2100 and compares
them with a read-only AstriumLab database:

```bat
python scripts\regress_node_stations.py C:\path\to\astrology.db
```

The database is a development-only regression oracle and is never included in
this repository or required by the deployed application.

## Deployment

The repository includes a `render.yaml` Blueprint for a free Render web
service. The application must be fully tested, licensed, reviewed for private
data, and made public before the Swiss Ephemeris-powered service is activated.

## Licensing

The project is intended to be distributed under the GNU Affero General Public
License, version 3. See `LICENSE` and `NOTICE.md`.
