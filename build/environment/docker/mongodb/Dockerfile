ARG CUSTOM_MONGODB_IMG=fetest/mongodb-fetest:tis
FROM ${CUSTOM_MONGODB_IMG}

COPY ./docker/mongodb/scripts/init-db.js /docker-entrypoint-initdb.d/init-db.js

# IMPORTANT: MongoDB automatically executes .js and .sh files in /docker-entrypoint-initdb.d/
# during container initialization ONLY on first run with empty /data/db directory.
# Similar to PostgreSQL behavior - scripts run only once when creating new database.
# If the database already exists, scripts are ignored.
