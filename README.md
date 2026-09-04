# La Volasfera Cycle Explorer

La Volasfera Cycle Explorer is a small Flask web application for examining
True North Node stationary points and converse astrological cycles. It is being
developed as a free companion tool for La Volasfera articles.

- [Use the hosted Cycle Explorer](https://la-volasfera-cycles.onrender.com/)
- [Read the illustrated introduction and instructions](https://lavolasferaastrology.substack.com/p/when-the-true-north-node-stands-still)
- [Read the calculation methodology](https://la-volasfera-cycles.onrender.com/methodology)

The hosted application runs on Render's Free plan, so its first page load after
a period of inactivity can take up to a minute. Running the application locally
avoids that delay and keeps all entered dates on your own computer.

## Project status

The public application includes a True Node calculation engine and a responsive
cycle-explorer interface. Converse timelines are shown by default; secondary,
tertiary and minor direct comparisons can be enabled separately.

## Run locally

The project is tested with Python 3.13.6. You need Python 3 and an internet
connection during the initial installation. Git is required only if you clone
the repository; alternatively, select **Code > Download ZIP** on GitHub and
extract the downloaded folder.

### Download the project with Git

```text
git clone https://github.com/hpatel36/la-volasfera-cycles.git
cd la-volasfera-cycles
```

If you downloaded the ZIP instead, open a terminal in the extracted project
folder (usually named `la-volasfera-cycles-main`) before continuing.

### Windows Command Prompt

```bat
py -3 -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python scripts\download_ephemeris.py
set EPHEMERIS_REQUIRED=true
set SE_EPHE_PATH=ephe
python -m flask --app app run
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\download_ephemeris.py
$env:EPHEMERIS_REQUIRED = "true"
$env:SE_EPHE_PATH = "ephe"
python -m flask --app app run
```

If PowerShell prevents `Activate.ps1` from running, use the Windows Command
Prompt instructions instead.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_ephemeris.py
export EPHEMERIS_REQUIRED=true
export SE_EPHE_PATH=ephe
python -m flask --app app run
```

### Open and stop the application

When the terminal displays `Running on http://127.0.0.1:5000`, open
<http://127.0.0.1:5000/> in your browser.

Keep the terminal open while using the application. To stop it cleanly, return
to the terminal and press **Ctrl+C**.

### Subsequent launches

You only need to create the virtual environment, install the dependencies and
download the ephemeris files once. On subsequent launches:

1. Open a terminal in the project folder.
2. Activate `.venv` using the command for your operating system above.
3. Set `EPHEMERIS_REQUIRED` and `SE_EPHE_PATH` again.
4. Run `python -m flask --app app run`.

If you update the local copy from GitHub and `requirements.txt` changes, run
`python -m pip install -r requirements.txt` again.

## Development checks

Install the development dependencies with:

```text
python -m pip install -r requirements-dev.txt
```

Run the tests with:

```text
python -m pytest
```

Run the strict deployment smoke test against downloaded ephemeris files with:

```text
python scripts/verify_release.py --ephe-path ephe
```

## Swiss Ephemeris data

True Node calculations from 1400 through 2100 require the lunar files
`semo_12.se1` and `semo_18.se1`. Binary `.se1` files are deliberately excluded
from Git. Download the exact tested versions with:

```text
python scripts/download_ephemeris.py
```

The downloader uses an official Swiss Ephemeris GitHub revision and verifies
both files with pinned SHA-256 checksums. Set `SE_EPHE_PATH` to use a different
local directory. Render downloads the files into `./ephe` during its build and
starts the application with strict validation enabled.

The local instructions above enable strict validation so the application stops
with an error rather than silently using fallback calculations if either file
is missing or incorrect.

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

## Project information

- [Methodology](https://la-volasfera-cycles.onrender.com/methodology)
- [Source references](SOURCES.md)
- [Third-party notices](NOTICE.md)
- [Complete licence](LICENSE)

## Licensing

Copyright © 2026 Harish Patel. This project is distributed under the GNU
Affero General Public License, version 3 or (at your option) any later version
(`AGPL-3.0-or-later`). See `LICENSE` and `NOTICE.md`.
