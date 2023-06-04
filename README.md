# Crossref-reconciliation-service
[![License](https://img.shields.io/github/license/jonasengelmann/crossref-reconciliation-service)](LICENSE)

[OpenRefine](http://openrefine.org) reconciliation service for [Crossref](https://www.crossref.org/).

Implemented query properties are `author` and `publication_year`. 

## Run via Docker (Recommended)

```console
docker build -t crossref-reconciliation-service .
docker run --rm -p 80:80 --env DOMAIN='http://localhost' crossref-reconciliation-service
```

The reconciliation service should now be accessible at [http://localhost](http://localhost). 

## Development

```console
pip3 install -r requirement.txt
```

Setup pre-commit hooks:
```console
pre-commit install
```

Start the reconciliation service:
```console
uvicorn main:app --reload --port 8000 --env-file .env.example
```

The reconciliation service should now be accessible at [http://localhost:8000](http://localhost:8000). 

## License

This project is licensed under MIT license - see the [LICENSE](LICENSE) file for more information.
