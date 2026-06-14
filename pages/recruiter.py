import streamlit as st
from agent.agent import run

st.title("Chat with the Candidate")
st.caption("Ask anything about the candidate's background, skills, or availability.")

if "history" not in st.session_state:
    st.session_state.history = []

# Display conversation
for msg in st.session_state.history:
    st.chat_message(msg["role"]).write(msg["content"])

# Input
user_input = st.chat_input("Ask a question...")
if user_input:
    # 1. Show the user's message on screen immediately
    st.chat_message("user").write(user_input)
    
    # 2. Run the agent while showing a spinner
    try:
        with st.spinner("Thinking..."):
            answer, updated_history, _ = run(st.session_state.history.copy(), user_input)
    except Exception as exc:  # surface a friendly message instead of a stack trace
        st.chat_message("assistant").error(
            "Sorry — I couldn't answer that just now. Please try again in a moment."
        )
        st.caption(f"(details: {type(exc).__name__})")
    else:
        # 3. Show the agent's answer immediately
        st.chat_message("assistant").write(answer)

        # 4. Save to state (no st.rerun needed, it will redraw naturally next turn)
        st.session_state.history = updated_history
