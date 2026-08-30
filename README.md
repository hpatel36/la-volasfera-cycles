# La Volasfera Cycle Explorer

La Volasfera Cycle Explorer is a small Flask web application for examining
True North Node stationary points and converse astrological cycles. It is being
developed as a free companion tool for La Volasfera articles.

## Project status

The Flask and Render foundation, True Node calculation engine and responsive
cycle-explorer interface are in place. Converse timelines are shown by default;
secondary, tertiary and minor direct comparisons can be enabled separately.

## Local development

The project currently uses Python 3.13.6.

```bat
py -3 -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
python -m flask --app app run --debug
```

Open <http://127.0.0.1:5000> in a browser. The health endpoint is available at
<http://127.0.0.1:5000/health>.

Run the tests with:

```bat
python -m pytest
```

Run the strict deployment smoke test against downloaded ephemeris files with:

```bat
python scripts\verify_release.py --ephe-path ephe
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
The default station selector uses a UTC-day-boundary event-selection method;
an exhaustive scanner is also available for inspecting every stable speed sign
change, including short-lived pairs outside that selection.

`calculations/cycles.py` supports transit, secondary, tertiary and minor
timelines in both direct and converse directions. Automated tests and a
full-range development regression validate the calculation engine; no database
is included in or required by the deployed application.

## Deployment

The repository includes a `render.yaml` Blueprint for a free Render web
service. Render uses the Python version pinned in `.python-version`, installs
only the runtime dependencies, downloads and validates the two ephemeris files,
and runs the application with Gunicorn. The service stores no submitted dates,
accounts or calculation results. Render's filesystem is ephemeral, which is
appropriate because the downloaded files are recreated on every build and the
application has no database or user uploads.

The repository must remain private until the final public-release review. Make
it public before activating the Swiss Ephemeris-powered service so every user
can obtain the corresponding AGPL source.

## Project information

- [Methodology](https://github.com/hpatel36/la-volasfera-cycles/blob/main/templates/information.html)
- [Source references](SOURCES.md)
- [Third-party notices](NOTICE.md)
- [Complete licence](LICENSE)

## Licensing

Copyright © 2026 Harish Patel. This project is distributed under the GNU
Affero General Public License, version 3 or (at your option) any later version
(`AGPL-3.0-or-later`). See `LICENSE` and `NOTICE.md`.
