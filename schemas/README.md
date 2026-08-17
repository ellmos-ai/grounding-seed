# Schema

`grounding-seed`'s local store (`store.py`) DELIBERATELY uses the same schema
as `source-resolver`: `ellmos.source-resolver.user-config.v1`.

No own JSON schema file here -- a second copy would be exactly the kind of
duplicate that can drift without anyone noticing. The canonical version lives
with `source-resolver`:

`https://github.com/ellmos-ai/source-resolver/blob/main/schemas/user-source-config.schema.json`

The identity is test-verified, not just claimed:
`tests/test_store.py::test_schema_id_matches_source_resolver_schema`.
