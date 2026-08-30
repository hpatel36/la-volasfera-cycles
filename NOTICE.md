# Third-party notices

## Swiss Ephemeris

The calculation engine uses Swiss Ephemeris through the `pysweph` Python
package. Swiss Ephemeris is developed by Astrodienst AG and is available under
a dual-licensing model that includes the GNU Affero General Public License.

The deployment build downloads `semo_12.se1` and `semo_18.se1` from official
Swiss Ephemeris repository commit
`b51a083390bf3cdc93a6ba466cbc83b846c4cfc4`. These are the pinned DE431 files
used to validate True Node stationary events from 1400 through 2100. Their
SHA-256 checksums are recorded and enforced in `calculations/ephemeris.py`.

Swiss Ephemeris source and licensing information:
<https://github.com/aloistr/swisseph>

La Volasfera Cycle Explorer is an independent project. It is not affiliated
with or endorsed by Astrodienst AG.

The complete application source is distributed under the GNU Affero General
Public License, version 3.
