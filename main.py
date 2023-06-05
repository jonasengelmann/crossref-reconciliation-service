import json
import os
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.cors import CORSMiddleware

from crossref_api_wrapper import CrossrefAPIWrapper

load_dotenv()

crossref_api = CrossrefAPIWrapper()

app = FastAPI(title="Crossref Reconciliation Service API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metadata = {
    "name": "Crossref Reconciliation Service",
    "defaultTypes": [],
    "identifierSpace": "http://localhost/identifier",
    "schemaSpace": "http://localhost/schema",
    "view": {"url": "https://search.crossref.org/?from_ui=yes&q={{id}}"},
    "preview": {
        "url": os.environ["DOMAIN"].strip("/") + "/preview?id={{id}}",
        "height": 250,
        "width": 350,
    },
    "suggest": {
        "property": {
            "service_url": os.environ["DOMAIN"].strip("/"),
            "service_path": "/suggest",
        }
    },
}


def process_queries(queries):
    query_batch = json.loads(queries)
    results = {}

    for key, query in query_batch.items():

        author, publication_year = None, None

        for property_ in query.get("properties", []):
            if property_["pid"] == "author":
                author = property_["v"]
            elif property_["pid"] == "publication_year":
                publication_year = property_["v"]

        crossref_results = crossref_api.search(
            title=query["query"],
            author=author,
            publication_type=query.get("type"),
            publication_year=publication_year,
        )

        result = []
        for x in crossref_results:
            record = {
                "id": x["record"]["DOI"],
                "name": x["record"]["title"][0],
                "score": x["score"],
                "match": True,
            }
            if type_ := x["record"].get("type"):
                record["type"] = [{"id": type_, "name": type_}]
            result.append(record)
        results[key] = {"result": result}
    return results


@app.post("/")
async def reconcile_post(request: Request):
    form = await request.form()
    if queries := form.get("queries"):
        return process_queries(queries)


@app.get("/")
def reconcile_get(callback: Optional[str] = None):
    if callback:
        content = f"{callback}({json.dumps(metadata)})"
        return Response(content=content, media_type="text/javascript")
    return metadata


@app.get("/queries")
def queries(queries: str):
    return process_queries(queries)


@app.get("/preview", response_class=HTMLResponse)
def preview(id: str):
    field_mapping = {
        "DOI": "DOI",
        "author": "Author(s)",
        "type": "Type",
        "published": "Publication Date",
        "publisher": "Publisher",
        "Container": "container-title",
    }

    metadata = crossref_api.find_by_doi(doi=id)
    html_metadata = ""
    for key, value in field_mapping.items():
        if x := metadata.get(key):
            if key == "author":
                x = "; ".join(
                    [f"{y.get('given', '')} " + f"{y.get('family', '')}" for y in x]
                )
            elif key == "published":
                x = metadata["published"]["date-parts"][0][0]
            elif key == "container":
                x = metadata.get("container-title", [""])[0]

            html_metadata += f"<p>{value}: {x}</p>"

    return f"""
    <html>
        <head><meta charset="utf-8" /></head>
        <body>
        <div style="font-weight:bold">
            {metadata['title'][0]}
        </div>
        <div style="font-size:12px">
            {html_metadata}
        </div>
        </body>
    </html>
    """


@app.get("/suggest")
def suggest(prefix: str):
    suggest_properties = [
        {
            "name": "author",
            "description": "Family name of first author.",
            "id": "author",
        },
        {
            "name": "publication year",
            "description": "Year of the publication.",
            "id": "publication_year",
        },
    ]
    result = []
    for x in suggest_properties:
        if prefix.lower() in x["name"].lower():
            result.append(x)

    return {"result": result}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
