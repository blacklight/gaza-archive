# gaza-archive

The purpose of this project is to provide a permanent archive of social media
posts from [verified accounts from Gaza](https://gaza-verified.org).

As censorship of Palestinian voices may mount also on decentralized social
media platforms just like it did on centralized ones, this archive is
intended to be a resource for future research and historical documentation.

This project will periodically scrape those profiles for new content and
archive any new activities, including their profiles metadata, all the public
posts and media attachments.

## Installation

```bash
cp ./backend/.env.example ./backend/.env
# WIP
# cp ./frontend/.env.example ./frontend/.env
# Modify .env files as needed
docker compose up
```

After the initial sync is completed you will be able to query data from the
SQLite database under `./data/app.db`, and all attachments will be stored under
`./data/media`, indexed by username.

## API

An OpenAPI specification is available at `/openapi.json` once the
backend is running.

If you run the service in docker-compose you can also access a Swagger UI at
`/swagger`.
