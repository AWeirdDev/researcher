const URI = "http://localhost:8080"

interface Result {
    content: string,
    done: boolean,
    background?: boolean,
}

export async function* ai(messages: any[]): AsyncGenerator<Result> {
    let res = await fetch(URI + "/conversation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })) }),
    });

    if (!res.body)
        throw new Error("there is no response body")

    let reader = res.body.getReader();
    let decoder = new TextDecoder();

    while (true) {
        let { done, value } = await reader.read();
        if (done) break;
        yield JSON.parse(decoder.decode(value));
    }
}