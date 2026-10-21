# Database setup

MongoDB indexes are initialized by `app.repositories.indexes.ensure_indexes` when the API starts. Add versioned migration scripts here when schema changes require backfills or coordinated rollout.
