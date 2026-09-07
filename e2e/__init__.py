"""Marks e2e/ as a package, mirroring tests/.

Not cosmetic. With pytest's default prepend import mode, the directory added to
sys.path for a test module is the first one ABOVE it without an __init__.py.
tests/ has one, so the repo root is added and `import agent` works. Without this
file, e2e/ itself was added instead, and CI failed at collection with
ModuleNotFoundError: No module named 'agent' — while passing locally, where the
working directory happened to be on sys.path already.
"""
