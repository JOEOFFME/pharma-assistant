# Immutable source data

The `osm_snapshot/` extract was fetched by the TASK 3 CLI. Raw response bytes
must not be edited by hand. `manifest.json` records query, endpoint, fetch/OSM
timestamps, response size and SHA256; the build rejects a hash mismatch.

© OpenStreetMap contributors. OSM source and derived database: ODbL 1.0.
https://www.openstreetmap.org/copyright
https://opendatacommons.org/licenses/odbl/1-0/

The query follows the OSM area tagged ISO3166-1=MA. This describes the selected
OSM query scope, not a verified complete national registry or a boundary claim.
The repository's processing code and offline rebuild commands are documented in
[data/pharmacies/README.md](../pharmacies/README.md).
