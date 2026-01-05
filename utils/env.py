import os


def load_env_var(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"Env var {name} is not set")
    return value
