# Git Workflow

AgentGuard uses a strict Git workflow to ensure the main branch remains stable and production-ready at all times.

## Branch Strategy

### Main Branch

**Branch:** `main`

**Purpose:** Production-ready code

**Rules:**
- Always stable
- Must pass all tests
- Must build successfully
- No direct development
- No experimental code
- No half-completed features
- Protected branch requiring PR approval

### Integration Branch

**Branch:** `integration`

**Purpose:** Integration testing before main merge

**Rules:**
- Multiple completed modules combined here
- Full test suite must pass
- Used to verify module interactions
- Merged to main only after all checks pass

**Workflow:**
```
feature/module → module tests → integration → full test suite → main
```

### Development Branches

#### Feature Branches

**Naming:** `feature/<module-name>` or `feature/<short-description>`

**Examples:**
- `feature/core-platform`
- `feature/agent-registry`
- `feature/agent-versioning`
- `feature/tool-registry`
- `feature/scenario-engine`
- `feature/execution-engine`
- `feature/sandbox-engine`
- `feature/trace-engine`
- `feature/evaluation-engine`
- `feature/failure-classifier`
- `feature/scoring-engine`
- `feature/regression-engine`
- `feature/recommendation-engine`
- `feature/reporting-engine`
- `feature/scheduler`
- `feature/browser-adapter`
- `feature/ci-integration`
- `feature/notifications`
- `feature/team-workspaces`

**Purpose:**
- Develop new features
- Implement new modules
- Add new capabilities

**Lifetime:** Until feature is complete and merged

#### Bug Fix Branches

**Naming:** `fix/<short-description>`

**Examples:**
- `fix/agent-validation-error`
- `fix/tool-registry-query`
- `fix/version-snapshot-bug`

**Purpose:**
- Fix bugs in existing features
- Address issues found in testing

**Lifetime:** Until fix is verified and merged

#### Refactoring Branches

**Naming:** `refactor/<short-description>`

**Examples:**
- `refactor/database-queries`
- `refactor/api-error-handling`
- `refactor/event-system`

**Purpose:**
- Code improvements without behavior changes
- Performance optimizations
- Code cleanup

**Lifetime:** Until refactoring is complete and verified

#### Hotfix Branches

**Naming:** `hotfix/<short-description>`

**Examples:**
- `hotfix/security-vulnerability`
- `hotfix/data-corruption`

**Purpose:**
- Urgent production fixes
- Critical security patches
- Data integrity issues

**Lifetime:** Very short - merge ASAP after verification

**Special Rules:**
- Can branch from `main` directly
- Can merge to `main` directly after thorough testing
- Should also merge back to `integration` and active feature branches

## Module Development Process

Every feature/module must follow this process:

### 1. Create Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/module-name
```

### 2. Define Module Contract

Create module documentation:
- `modules/<module-name>/README.md`
- Interface definitions
- Domain models
- Public API contracts
- Event contracts

### 3. Implement Module

Write module implementation:
- Domain logic
- Application services
- Infrastructure adapters
- API endpoints

### 4. Write Unit Tests

Test individual components:
- Domain logic
- Service methods
- Utility functions

### 5. Write Integration Tests

Test module as a whole:
- API endpoints
- Database operations
- External integrations

### 6. Run Existing Regression Suite

Ensure no existing functionality is broken:
```bash
make test
```

### 7. Run Lint/Type Checks

Ensure code quality:
```bash
make lint
make typecheck
```

### 8. Run Build

Ensure project builds:
```bash
make build
```

### 9. Commit and Push

```bash
git add .
git commit -m "feat(module-name): description"
git push origin feature/module-name
```

### 10. Create Pull Request to Integration

Create PR from `feature/module-name` → `integration`

PR must include:
- Description of changes
- Module documentation link
- Test coverage report
- Breaking changes (if any)
- Migration steps (if any)

### 11. Integration Testing

After merge to `integration`, verify:
- All tests pass
- No module conflicts
- API contracts honored
- Database migrations work
- Frontend builds
- Docker compose works

### 12. Merge to Main

After integration verification:
- Create PR from `integration` → `main`
- Require approvals
- All CI checks must pass
- Squash merge or regular merge (team decision)

## Commit Message Convention

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `test` - Test changes
- `docs` - Documentation
- `chore` - Maintenance
- `perf` - Performance improvement
- `style` - Code style changes
- `ci` - CI/CD changes

**Examples:**
```
feat(agent-registry): add agent creation endpoint
fix(tool-registry): correct risk level validation
refactor(core): improve event bus performance
test(versioning): add version snapshot tests
docs(api): update API contract documentation
```

## Branch Protection Rules

### Main Branch

- ✅ Require pull request before merging
- ✅ Require approvals (1+)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Require conversation resolution
- ❌ Allow force pushes
- ❌ Allow deletions

**Required Status Checks:**
- Backend lint
- Backend type check
- Backend tests
- Frontend lint
- Frontend type check
- Frontend tests
- Integration tests
- Build verification

### Integration Branch

- ✅ Require pull request before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ❌ Allow force pushes
- ❌ Allow deletions

## Merge Conflicts

### Resolution Strategy

1. **Update feature branch from main:**
   ```bash
   git checkout feature/module-name
   git fetch origin
   git merge origin/main
   # Resolve conflicts
   git commit
   git push
   ```

2. **Prefer module isolation:**
   - If conflicts arise, modules may be too coupled
   - Review module boundaries
   - Refactor if necessary

3. **Never force push to shared branches:**
   - No `git push --force` to integration or main
   - No history rewriting after push

## Release Process

### Versioning

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Release Branch

**Naming:** `release/v1.2.3`

**Process:**
1. Branch from `main`
2. Update version numbers
3. Update CHANGELOG
4. Final testing
5. Merge to `main`
6. Tag release
7. Merge back to `integration`

### Tagging

```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

## Emergency Procedures

### Reverting a Merge

If a merged feature breaks production:

```bash
git checkout main
git revert -m 1 <merge-commit-hash>
git push origin main
```

Then:
1. Fix issue in feature branch
2. Re-test thoroughly
3. Re-submit PR

### Rolling Back

For critical issues:
1. Identify last known good commit
2. Create hotfix branch
3. Revert problematic changes
4. Thorough testing
5. Emergency merge to main

## Best Practices

### Do ✅

- Keep commits atomic and focused
- Write descriptive commit messages
- Update tests with code changes
- Run full test suite before PR
- Keep branches up to date with main
- Delete branches after merge
- Review your own PR before requesting reviews
- Respond to PR comments promptly
- Test migrations locally

### Don't ❌

- Commit secrets or credentials
- Push directly to main
- Force push to shared branches
- Leave failing tests
- Ignore CI failures
- Merge without approval
- Skip code review
- Commit large binary files
- Mix unrelated changes in one commit
- Leave merge commits unresolved

## CI/CD Integration

Every push triggers:
1. Linting
2. Type checking
3. Unit tests
4. Integration tests (on PR to integration/main)
5. Build verification
6. Security scanning

Failed checks block merge.

## Module Branch Strategy

Each major module should have its own feature branch:

```
main
├── feature/core-platform
├── feature/agent-registry
├── feature/agent-versioning
├── feature/tool-registry
├── feature/scenario-engine
├── feature/execution-engine
└── ...
```

Modules can be developed in parallel, then integrated through the `integration` branch.

## Questions?

Contact the platform team or refer to:
- [Architecture Documentation](./architecture.md)
- [Module Boundaries](./module-boundaries.md)
- [Testing Strategy](./testing-strategy.md)
