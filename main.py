import streamlit as st

pg = st.navigation([
    st.Page("pages/setup.py", title="Candidate Setup"),
    st.Page("pages/recruiter.py", title="Recruiter Chat")
])
pg.run()
