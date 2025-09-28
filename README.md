# gaza-archive

The purpose of this project is to provide a permanent archive of social media
posts from [verified accounts from Gaza](https://gaza-verified.org).

As censorship of Palestinian voices may mount also on decentralized social
media platforms just like it did on centralized ones, this archive is
intended to be a resource for future research and historical documentation.

This project will periodically scrape those profiles for new content and
archive any new activities, including their profiles metadata, all the public
posts and media attachments.

The official mirror of the archive is available at
[archive.gaza.onl](https://archive.gaza.onl).

## Installation

```bash
cp .env.example .env
# Modify .env file as needed

# Build the frontend files (this should only be required once, or when the
# frontend code is updated)
make

# Start all the services
docker compose up
```

After the initial sync is completed you will be able to query data from the
SQLite database under `./data/app.db`, and all attachments will be stored under
`./data/media`, indexed by username.

## Web interface

After starting the services, and after the initial sync is completed, you can
access a web interface at `http://localhost:8000` to browse the archived content.

## Browse raw media

After starting the services, and after the initial sync is completed, you can
browse the raw media files at `http://localhost:8000/media`, indexed by user
handle.

## API

An OpenAPI specification is available at
`http://localhost:8000/api/v1/openapi.json` once the backend is running.

If you run the service in docker-compose you can also access a Swagger UI at
`http://localhost:8000/swagger`.
