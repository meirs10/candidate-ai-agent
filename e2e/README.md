# End-to-end smoke test

Run separately from the unit suite:

```bash
pytest e2e/ -v
```

It lives outside `tests/` on purpose. To exercise the agent without any external
service, it replaces `rag.retriever`, `chromadb` and friends in `sys.modules`
*before* importing project code — which is the only point at which that mocking
can work, since `agent.agent` imports the retriever at module load.

Those substitutions are global and permanent for the interpreter. Collected in
the same pytest session as `tests/test_retriever.py`, the mock module shadows the
real one and that suite fails to import. Keeping this file out of `testpaths`
means the unit suite never sees the mocks, and CI runs the two as separate steps.
