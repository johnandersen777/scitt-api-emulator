import json
import pathlib
import logging
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent
from pydantic import BaseModel, Field
from pycose.messages import Sign1Message


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# class SCITTSignalsFederationCreatedEntry:
class SCITTSignalsFederationCreatedEntry(BaseModel):
    tree_alg: str
    entry_id: str
    # receipt: bytes
    # statement: bytes
    statement_object: dict
    public_service_parameters: dict


app = FastAPI()


workspace_path = pathlib.Path(__file__).parent.joinpath("workspace")
storage_path = workspace_path.joinpath("storage")
service_parameters_path = workspace_path.joinpath("service_parameters.json")
service_parameters_text = service_parameters_path.read_text()
service_parameters = json.loads(service_parameters_text)
tree_alg = service_parameters["treeAlgorithm"]
# define some entries
# TODO Load from Bovine
entries = []
for statement_path in storage_path.glob("*.cose"):
    entry_id = statement_path.stem
    statement = statement_path.read_bytes()
    msg = Sign1Message.decode(statement, tag=True)
    try:
        statement_object = json.loads(msg.payload.decode())
    except:
        try:
            statement_object = {"payload": msg.payload.decode()}
        except:
            statement_object = {"payload": str(repr(msg.payload))}
    receipt_path = statement_path.with_suffix(".receipt.cbor")
    receipt = receipt_path.read_bytes()
    entries.append(
        SCITTSignalsFederationCreatedEntry(
            tree_alg=tree_alg,
            entry_id=entry_id,
            # receipt=receipt,
            statement_object=statement_object,
            public_service_parameters=service_parameters,
        )
    )


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def entries_table() -> list[AnyComponent]:
    """
    Show a table of four entries, `/api` is the endpoint the frontend will connect to
    when a entry visits `/` to fetch components to render.
    """
    return [
        c.Page(  # Page provides a basic container for components
            components=[
                c.Heading(text="SCITT UI", level=1),
                c.Markdown(
                    text="\nDocumentation: [https://scitt.unstable.chadig.com](https://scitt.unstable.chadig.com)\n\n",
                ),
                c.Heading(text="Entries", level=2),  # renders `<h2>Entries</h2>`
                c.Table[
                    SCITTSignalsFederationCreatedEntry
                ](  # c.Table is a generic component parameterized with the model used for rows
                    data=entries,
                    # define two columns for the table
                    columns=[
                        # the first is the entries, name rendered as a link to their profile
                        DisplayLookup(
                            field="entry_id",
                            on_click=GoToEvent(url="/entry/{entry_id}/"),
                        ),
                    ],
                ),
            ]
        ),
    ]


@app.get(
    "/api/entry/{entry_id}/", response_model=FastUI, response_model_exclude_none=True
)
def entry_profile(entry_id: str) -> list[AnyComponent]:
    """
    User profile page, the frontend will fetch this when the entry visits `/entry/{id}/`.
    """
    try:
        entry = next(u for u in entries if u.entry_id == entry_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Entry not found")
    return [
        c.Page(
            components=[
                c.Heading(text=entry.entry_id, level=2),
                c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
                c.Heading(text="Statement Object", level=4),
                c.Markdown(
                    text=f"```json\n{json.dumps(entry.statement_object, indent=4, sort_keys=True)}\n```"
                ),
                c.Heading(text="Service Parameters", level=4),
                c.Markdown(
                    text=f"```json\n{json.dumps(entry.public_service_parameters, indent=4, sort_keys=True)}\n```"
                ),
            ]
        ),
    ]


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title="SCITT Entries"))
