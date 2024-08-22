const URI = "http://localhost:8080"

export async function ai(messages: any[]): Promise<string> {
    console.log(messages);
    let res = await fetch(URI + "/conversation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages }),
    });

    if (!res.ok)
        throw new Error("Failed to fetch ai" + res.statusText)

    return (await res.json())['result']
}