import asyncio
import os
from typing import List, Literal

import ddginternal
import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from pydantic import BaseModel

from preprompt import get_prompt

dotenv.load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])


@app.get("/")
async def index():
    return {"message": "Hi mom!"}


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Request(BaseModel):
    messages: List[Message]


@app.post("/conversation")
async def conversation(req: Request):
    qres = await groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": get_prompt("searcher").format(
                    conversation="\n".join(
                        [msg.role.title() + ": " + msg.content for msg in req.messages]
                    )
                ),
            }
        ],
    )
    content = qres.choices[0].message.content
    assert content, "No content (qres)"

    meta = ""
    if content.strip().strip("\"'.").lower() != "null":
        result = await asyncio.to_thread(ddginternal.search, content)
        if result.abstract:
            meta += f"Abstract:\n{result.abstract}\n"

        if result.web:
            meta += "Web results:" + "\n".join(
                [w.title + "\n" + w.description.strip() for w in result.web]
            )

        meta = meta.strip()

    msgs = [msg.model_dump() for msg in req.messages]
    res = await groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": get_prompt("core"),
            },
        ]
        + msgs[:-1]  # type: ignore
        + ([{"role": "system", "content": f"WEB RESOURCES:\n{meta}"}] if meta else [])
        + [msgs[-1]],
    )
    content = res.choices[0].message.content
    assert content, "No content"

    return {"result": content}


# uvicorn main:app --host=0.0.0.0 --port=8080
