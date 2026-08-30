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

## Deployment

The repository includes a `render.yaml` Blueprint for a free Render web
service. The application must be fully tested, licensed, reviewed for private
data, and made public before the Swiss Ephemeris-powered service is activated.

## Licensing

The project is intended to be distributed under the GNU Affero General Public
License, version 3. See `LICENSE` and `NOTICE.md`.

