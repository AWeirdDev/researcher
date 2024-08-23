import asyncio
import json
import os
from typing import List, Literal

import ddginternal
import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


def parse_messages(messages: List[Message]) -> List[dict]:
    results = []
    for message in messages:
        if message.role == "assistant":
            is_long = "\n" in message.content.strip()
            results.append(
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "type": ("long" if is_long else "short"),
                            **(
                                {"long_answer": message.content.strip().split("\n")}
                                if is_long
                                else {"answer": message.content.strip()}
                            ),
                        },
                        indent=2
                    ),
                }
            )

        results.append({"role": message.role, "content": message.content})

    return results


@app.post("/conversation")
async def conversation(req: Request):
    async def ai(messages: list) -> dict:
        res = await groq.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": get_prompt("core"),
                },
            ]
            + messages,  # type: ignore
        )
        content = res.choices[0].message.content
        assert content, "No content"

        try:
            c = content.strip("`,]") + ("}" if content.endswith(("]", '"')) else "")
            if c.startswith("{"):
                result = json.loads(c[:-1] if c.endswith("}}") else c)
            else:
                result = {"type": "short", "answer": c}
        except json.JSONDecodeError as err:
            print(err)
            print(content)
            return {"type": "error", "content": "Error: Maoyue is having a stroke!"}

        return result

    async def streamer():
        messages = parse_messages(req.messages)

        while True:
            ai_res = await ai(messages)

            if ai_res["type"] in {"long", "short"}:
                print(ai_res)
                yield json.dumps(
                    {
                        "content": (
                            ai_res["answer"]
                            if ai_res["type"] == "short"
                            else "\n".join(ai_res["long_answer"])
                        ),
                        "done": True,
                    }
                )
                break

            elif ai_res["type"] == "search":
                yield json.dumps({"content": ai_res["task_name"], "done": False})
                t = ""
                result = await asyncio.to_thread(ddginternal.search, ai_res["query"])
                if result.abstract:
                    t += "Abstract:\n" + result.abstract.text + "\n"  # type: ignore

                if result.news:
                    t += "News:\n" + "\n\n".join(
                        [n.title + "\n" + n.excerpt for n in result.news[:5]]
                    )

                t += "Web results:\n" + "\n\n".join(
                    [w.title + "\n" + w.description for w in result.web[:5]]
                )
                messages.append(
                    {"role": "assistant", "content": json.dumps(ai_res, indent=2)}
                )
                wr = {
                    "role": "user",
                    "content": "WEB SEARCH RESULTS:\n"
                    + t.strip()
                    + "\nSummarize the results.",
                }
                messages.append(wr)
                yield json.dumps(
                    {"content": wr["content"], "done": False, "background": True}
                )

            elif ai_res["type"] == "error":
                yield json.dumps({"content": ai_res["content"], "done": True})
                break

    return StreamingResponse(streamer(), media_type="text/event-stream")


# uvicorn main:app --host=0.0.0.0 --port=8080
