# Schema

`grounding-seed`'s lokaler Speicher (`store.py`) verwendet ABSICHTLICH dasselbe
Schema wie `source-resolver`: `ellmos.source-resolver.user-config.v1`.

Keine eigene JSON-Schema-Datei hier -- eine zweite Kopie waere genau die Art
Duplikat, die driften kann, ohne dass es auffaellt. Die kanonische Fassung liegt
bei `source-resolver`:

`C:\_Local_DEV\repos\source-resolver\schemas\user-source-config.schema.json`

Die Identitaet ist testgesichert, nicht nur behauptet:
`tests/test_store.py::test_schema_id_matches_source_resolver_schema`.
