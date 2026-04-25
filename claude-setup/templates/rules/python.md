# Python Rules

## Style
- Follow PEP 8. Use `ruff` for linting, `ruff format` for formatting.
- Type hints required for function signatures. Use `mypy --strict` or `pyright`.
- Prefer `pathlib.Path` over `os.path`.
- Use f-strings over `.format()` or `%`.
- Docstrings: Google style for public APIs. Skip for obvious private methods.

## Structure
- One class per file when the class is substantial (>50 lines).
- Group imports: stdlib → third-party → local. Use `isort` or ruff's import sorting.
- Use `__all__` in `__init__.py` to define public API.

## Error Handling
- Catch specific exceptions, never bare `except:`.
- Use custom exception classes for domain errors.
- Log errors with context (what failed, with what input).
- For CLI tools: catch at the top level, print user-friendly messages.

## Testing
- Use `pytest`. Test files mirror source structure: `src/foo/bar.py` → `tests/foo/test_bar.py`.
- Name tests descriptively: `test_login_fails_with_expired_token`.
- Use fixtures for setup, parametrize for variations.
- Mock external services, not internal logic.

## AI/ML Specific
- Use `torch.no_grad()` for inference, never training.
- Pin random seeds for reproducibility: `torch.manual_seed()`, `np.random.seed()`, `random.seed()`.
- Log hyperparameters and metrics with every experiment run.
- Use `tqdm` for progress bars in long-running operations.
- Prefer `datasets` (HuggingFace) for data loading when applicable.
- GPU memory: explicitly move tensors to device, use `del` + `torch.cuda.empty_cache()` when needed.

## Dependencies
- Use `pyproject.toml` for project config (PEP 621).
- Pin versions in `requirements.txt` or `uv.lock`.
- Prefer `uv` over `pip` for faster installs.
