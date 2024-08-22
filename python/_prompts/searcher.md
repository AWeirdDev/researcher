Given conversation context, you will determine what to search.
Example 1:
User: do you like badminton?
You: null

You use 'null' when this is just a regular message and it's possible to not use search.

Example 2:
User: do you like badminton?
Assistant: Yes! I love badminton, too!
User: who won the 2024 olympics?
You: 2024 olympics badminton results

You respond with a fitting query. NEVER use URL-encoded strings.

Given conversation:
{conversation}
What's the search query, or just "null?" NEVER add descriptions.