__prompts__ = {}


def get_prompt(name: str) -> str:
    if name not in __prompts__:
        with open(f"_prompts/{name}.md", "r", encoding="utf-8") as f:
            __prompts__[name] = f.read()

    return __prompts__[name]
