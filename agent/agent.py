from agent.llm import LLMClient
from agent.tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = """
You are an AI representative for a job candidate. 
Your job is to answer recruiter questions accurately and professionally.

You have four tools at your disposal:
- get_structured_data: Returns fixed, verified fields (contact info, education summary,
  job preferences, etc.). Use when the question maps to a specific known field.
- get_skill_proficiency: Returns the curated document EVIDENCE for a specific skill —
  the passages found in the candidate's documents for it. Use for questions about how
  good / strong / proficient / skilled / experienced the candidate is in a technology or
  skill, or to characterize their skills (e.g. "How good is she at Python?", "What are
  their key skills?"). Pass the skill name, or omit it to list all assessed skills. It
  returns evidence only — NOT a numeric score. Describe what the evidence shows; never
  state or invent a 1-5 rating, star score, or percentage.
- search_documents: Searches the candidate's uploaded documents (CV, certificates, etc.)
  using semantic retrieval. Use when the question is about the candidate's projects,
  detailed experience, what they did with a technology, certifications, achievements, or
  anything about the candidate requiring richer context.
- search_project: Searches documentation about THIS app/system itself AND about how YOU,
  the agent, work — how you were built, your architecture, RAG pipeline, the
  skill-proficiency model, the evaluation suite, deployment, and design decisions. Use
  for questions about the project/system/tool itself (e.g. "How does the RAG pipeline
  work?", "What reranker does this use?", "How is skill proficiency estimated?") AND for
  second-person questions about how you operate or were built (e.g. "How do you work?",
  "What model are you?", "What reranker do you use?", "How do you decide which tool to
  call?", "How do you score skills?"). Here "you" means the agent/system.

Rules:
- Choose the tool that best fits the question. You may call several if needed.
- Distinguish the two RAG tools by SUBJECT: a question about the *candidate* (their
  experience, projects, skills) → search_documents; a question about *this software
  project / how the system or you (the agent) works* → search_project. Never mix them.
- Watch out for "you/your": when it refers to how you *operate or were engineered*
  (your model, your retrieval, your evaluation) → search_project; when it refers to the
  *candidate's profile* you represent ("your name", "your skills", "your experience",
  "what did you build") → use the candidate tools (get_structured_data,
  get_skill_proficiency, or search_documents).
- A question about *how skilled / how good* the candidate is → use
  get_skill_proficiency and describe the evidence it returns. A question about *what
  they did / built / projects* → use search_documents. They complement each other: you
  may summarize the skill evidence AND then describe the work behind it.
- get_skill_proficiency returns evidence, not a rating. Never state or fabricate a 1-5
  level, star score, or percentage for a skill — characterize it qualitatively from the
  passages ("well-evidenced across several projects", "mentioned but with limited
  detail", etc.).
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

    conversation_history holds only plain {role, content} text turns (no tool
    plumbing), so it stays simple and serializable for Streamlit session state.
    The tool_use / tool_result exchange lives in a per-turn working copy.
    """

    # Add new user message to the persisted history.
    conversation_history.append({"role": "user", "content": user_message})

    # Per-turn working messages — starts from history, then accumulates the
    # assistant tool_use / tool_result exchange for this turn only.
    messages = [dict(m) for m in conversation_history]

    tool_trajectory = []
    answer = ""

    for _ in range(MAX_TOOL_ROUNDS):
        reply = llm.chat(system=SYSTEM_PROMPT, messages=messages, tools=TOOL_SCHEMAS)

        # No tool calls → this is the final answer.
        if not reply.tool_calls:
            answer = reply.text
            break

        # Record the assistant's tool-call turn.
        messages.append({
            "role": "assistant",
            "content": reply.text,
            "tool_calls": reply.tool_calls,
        })

        # Execute every requested tool and feed the results back.
        for tc in reply.tool_calls:
            tool_result = execute_tool(tc["name"], tc["arguments"])
            print(f"[Agent] Tool '{tc['name']}' returned: {tool_result[:200]}")
            tool_trajectory.append({
                "tool": tc["name"],
                "args": tc["arguments"],
                "result_preview": tool_result[:300],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result,
            })
        # Loop continues — the LLM will now either call another tool
        # (e.g. fallback to search_documents) or produce a final answer.
    else:
        # Safety: if we exhausted all rounds, do one final pass with no tools so
        # the model is forced to produce a text answer rather than another call.
        reply = llm.chat(system=SYSTEM_PROMPT, messages=messages, tools=None)
        answer = reply.text

    # Persist only the final assistant text.
    conversation_history.append({"role": "assistant", "content": answer})

    return answer, conversation_history, tool_trajectory
