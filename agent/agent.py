from agent.llm import LLMClient
from agent.tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = """
You are an AI representative for a job candidate.
Your job is to answer recruiter questions accurately and professionally.

You have three tools at your disposal:
- get_structured_data: Returns fixed, verified fields (contact info, education summary,
  job preferences, etc.). Use when the question maps to a specific known field.
- get_skill_proficiency: Returns the candidate's proficiency LEVEL (1-5) in a specific
  skill, inferred from their documents by a trained scoring model, with the supporting
  evidence. Use for questions about how good / strong / proficient / skilled / experienced
  the candidate is in a technology or skill, to rate a skill, or to rank their skills
  (e.g. "How good is she at Python?", "What are their strongest skills?"). Pass the skill
  name, or omit it to list all assessed skills with their levels.
- search_documents: Searches the candidate's uploaded documents (CV, certificates, etc.)
  using semantic retrieval. Use when the question is about projects, detailed experience,
  what they did with a technology, certifications, achievements, or anything requiring
  richer context.

Rules:
- Choose the tool that best fits the question. You may call several if needed.
- A question about a *proficiency level / how skilled* the candidate is → use
  get_skill_proficiency. A question about *what they did / built / projects* → use
  search_documents. They complement each other: you may report the level AND then
  describe the work behind it.
- If a tool's result is incomplete or doesn't fully answer the question, call another
  tool before responding. For example, if get_skill_proficiency says a skill was not
  assessed, fall back to search_documents.
- Never guess or make up information. If you don't find it, say so.
- Keep answers concise and professional.
- Always answer in the same language the recruiter used.
"""

MAX_TOOL_ROUNDS = 5  # safety cap to prevent infinite loops

llm = LLMClient()


def run(conversation_history: list, user_message: str) -> tuple[str, list, list]:
    """
    Main agent turn.
    Supports multiple sequential tool calls so the LLM can fall back
    from structured data to document search when needed.
    Returns (answer_text, updated_conversation_history, tool_trajectory)

    tool_trajectory is a list of dicts:
        [{"tool": "get_structured_data", "args": {"field": "full_name"},
          "result_preview": "full_name: Ofir Ohan"}]
    """

    # Add new user message to history
    conversation_history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *conversation_history]

    tool_trajectory = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = llm.call(messages=messages, tools=TOOL_SCHEMAS)
        message = response["message"]
        print("OLLAMA RAW MESSAGE:", message)

        # If no tool call, we have our final answer
        if not message.get("tool_calls"):
            answer = message["content"]
            break

        # Execute each tool call the LLM requested
        tool_call = message["tool_calls"][0]
        tool_name = tool_call["function"]["name"]
        tool_args = tool_call["function"]["arguments"]

        tool_result = execute_tool(tool_name, tool_args)
        print(f"[Agent] Tool '{tool_name}' returned: {tool_result[:200]}")

        # Record the tool call in the trajectory
        tool_trajectory.append(
            {
                "tool": tool_name,
                "args": tool_args,
                "result_preview": tool_result[:300],
            }
        )

        # Append the tool interaction so the LLM sees the result
        messages.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
        messages.append({"role": "tool", "content": tool_result})

        # Loop continues — the LLM will now either call another tool
        # (e.g. fallback to search_documents) or produce a final answer.
    else:
        # Safety: if we exhausted all rounds, do one final call without tools
        response = llm.call(messages=messages)
        answer = response["message"]["content"]

    # Update conversation history
    conversation_history.append({"role": "assistant", "content": answer})

    return answer, conversation_history, tool_trajectory
