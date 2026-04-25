# Go Rules

## Style
- Follow `gofmt` and `goimports` — non-negotiable.
- Use `golangci-lint` with default config.
- Variable names: short in small scopes (`i`, `err`), descriptive in larger scopes.
- Exported names get doc comments. Unexported names don't need them unless tricky.

## Structure
- Package names: short, lowercase, no underscores. Avoid `util`, `common`, `misc`.
- One file per major type/concern. Don't split too early.
- `internal/` for code that shouldn't be imported externally.
- `cmd/` for CLI entry points, each in its own subdirectory.

## Error Handling
- Always check errors. Never `_ = someFunc()` for error returns.
- Wrap errors with context: `fmt.Errorf("failed to process %s: %w", name, err)`.
- Use sentinel errors (`var ErrNotFound = errors.New(...)`) for expected conditions.
- Custom error types only when callers need to inspect error details.

## Testing
- Table-driven tests as default pattern.
- `_test.go` in the same package for whitebox, `_test` package for blackbox.
- Use `testify/assert` or stdlib `testing` — pick one per project.
- Test names: `TestFuncName_condition_expectedResult`.

## Concurrency
- Prefer channels over shared memory with mutexes.
- Always use `context.Context` for cancellation and timeouts.
- `errgroup` for parallel work with error propagation.
- Never start goroutines without a way to stop them.

## Performance
- Profile before optimizing: `pprof`, `trace`.
- Use `sync.Pool` for frequently allocated objects.
- Avoid allocations in hot paths — pre-allocate slices with `make([]T, 0, capacity)`.
- Use `strings.Builder` for string concatenation in loops.

## Dependencies
- Minimize external dependencies. stdlib is extensive — use it.
- `go mod tidy` before every commit.
- Pin indirect dependency versions in `go.sum`.
