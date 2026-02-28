# Playbook: Phase 2 — Template Skill

**Status:** active  
**Phase:** 2  
**Date:** 2026-02-28  

---

## Purpose

Documents the canonical `_template` skill skeleton and GHCR image build/push workflow. This template enables fast, consistent skill generation by providing a ready-to-copy skeleton that satisfies the [skill standard](https://github.com/8r4n/deerflow-skills/blob/main/docs/skill-standard.md).

---

## 1. Template Skill Skeleton

### 1.1 Location

The template lives at `skills/_template/` in `deerflow-ops`:

```
skills/_template/
├── README.md            ← documentation template (required sections)
├── Dockerfile           ← container image build (Python 3.12-slim)
├── skill.yaml           ← manifest (name, version, tools, runtime, env)
├── Makefile             ← build, run, test, and GHCR push targets
├── requirements.txt     ← Python dependencies (pin versions)
└── tests/
    ├── __init__.py
    └── test_contract.py ← contract test skeleton
```

### 1.2 Required files per skill standard

| File | Purpose |
|------|---------|
| `README.md` | Purpose, build/run instructions, tools exposed, env vars, troubleshooting |
| `Dockerfile` | Builds a "blessed" container image |
| `skill.yaml` | Machine-readable manifest (name, version, tools, runtime, env, mounts) |
| `tests/` | Contract tests: server starts, tool endpoints respond, error handling works |

### 1.3 How to create a new skill

1. **Copy the template** from `deerflow-ops` into your local clone of `deerflow-skills`:
   ```bash
   cp -r /path/to/deerflow-ops/skills/_template /path/to/deerflow-skills/skills/<new-skill-name>
   ```

2. **Replace placeholders** — search for `<skill-name>` in all files and replace with the actual name.

3. **Implement the skill** — add application code, update `requirements.txt`, and flesh out the Dockerfile.

4. **Update `skill.yaml`** — fill in the real tool names, version, runtime config, and env vars.

5. **Write contract tests** — add tests that validate tool endpoints beyond the skeleton checks.

6. **Build and test locally**:
   ```bash
   cd skills/<new-skill-name>
   make build
   make test
   ```

7. **Push to GHCR**:
   ```bash
   make push        # pushes :version and :latest
   make tag-sha     # also pushes :sha-<short-sha>
   ```

8. **Open a PR** in `8r4n/deerflow-skills` and create a `memory:skill` issue in `8r4n/deerflow-ops`.

---

## 2. GHCR Image Build and Push

### 2.1 Image naming convention

```
ghcr.io/8r4n/deerflow-skills/<skill-name>:<tag>
```

Tags:
- `<version>` — semantic version from `skill.yaml` (e.g., `0.1.0`)
- `latest` — most recent build on the default branch
- `sha-<short-sha>` — git commit-based tag for traceability

### 2.2 Makefile targets

| Target | Description |
|--------|-------------|
| `make build` | Build the Docker image with version and latest tags |
| `make run` | Build and run the container locally (port 8080) |
| `make test` | Build and run contract tests inside Docker |
| `make push` | Push `:version` and `:latest` tags to GHCR |
| `make tag-sha` | Tag with `:sha-<short-sha>` and push |
| `make clean` | Remove local images |

### 2.3 Authentication

**In Codespaces:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

The devcontainer post-create command handles this automatically.

**In GitHub Actions:**
The `.github/workflows/ghcr-publish.yml` workflow handles authentication via `docker/login-action@v3`.

### 2.4 CI workflow reference

The existing `.github/workflows/ghcr-publish.yml` in `deerflow-ops` provides the reference pattern for GitHub Actions-based GHCR publishing. For per-skill CI in `deerflow-skills`, use the same authentication and tagging pattern with the skill's Makefile.

---

## 3. Skill Completeness Score (SCS)

A skill is considered "shippable" when:

- [ ] All required files exist (`README.md`, `Dockerfile`, `skill.yaml`, `tests/`)
- [ ] README contains all required sections (purpose, build/run, tools, env vars, troubleshooting)
- [ ] Contract tests pass (`make test`)
- [ ] Image builds successfully (`make build`)
- [ ] A `memory:skill` issue exists in `deerflow-ops` with verification evidence

---

## Verification

- [ ] `skills/_template/` directory exists with all required files
- [ ] Template Dockerfile builds (with placeholder code replaced)
- [ ] Template contract tests validate file structure when run
- [ ] Makefile targets reference correct GHCR registry path
- [ ] Playbook documents the full workflow from template to published image

---

## Related resources

- [Skill standard](https://github.com/8r4n/deerflow-skills/blob/main/docs/skill-standard.md)
- [Phase 1 playbook](playbook-phase1-tooling.md)
- [GHCR publish workflow](../.github/workflows/ghcr-publish.yml)
- [Label taxonomy](labels.md)
- [System whitepaper](whitepaper.md)
