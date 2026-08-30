# La Volasfera Cycle Explorer

La Volasfera Cycle Explorer is a small Flask web application for examining
True North Node stationary points and converse astrological cycles. It is being
developed as a free companion tool for La Volasfera articles.

## Project status

The Flask and Render foundation is in place. The calculation engine will be
added only after its outputs have been locked down with regression examples
from the private AstriumLab desktop application.

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

## Deployment

The repository includes a `render.yaml` Blueprint for a free Render web
service. The application must be fully tested, licensed, reviewed for private
data, and made public before the Swiss Ephemeris-powered service is activated.

## Licensing

The project is intended to be distributed under the GNU Affero General Public
License, version 3. See `LICENSE` and `NOTICE.md`.
