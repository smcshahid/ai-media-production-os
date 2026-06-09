-- T-02-02 — PostgreSQL first-boot initialization.
--
-- This script runs once via the official postgres image entrypoint
-- (/docker-entrypoint-initdb.d) against the database named by POSTGRES_DB,
-- after the image has already created the POSTGRES_USER and POSTGRES_DB.
--
-- Keep statements idempotent (IF NOT EXISTS) so re-running them by hand on an
-- existing database is safe.

-- uuid-ossp: server-side UUID generation for primary keys (US-04 schema).
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pgcrypto: gen_random_uuid() and hashing helpers used by lineage/audit work.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
