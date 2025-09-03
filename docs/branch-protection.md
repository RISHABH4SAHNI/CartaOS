# Branch Protection and Development Workflow

## Dev Branch Configuration

### 1. Branch Protection Rules
1. Navigate to: `Settings` > `Branches` > `Branch protection rules` > `Add rule`
2. Apply to branch: `dev`
3. Enable the following protections:
   - [ ] Require a pull request before merging
     - [ ] Require approvals (Required number: 1)
     - [ ] Dismiss stale pull request approvals when new commits are pushed
   - [ ] Require status checks to pass before merging
     - [ ] Require branches to be up to date before merging
     - [ ] Status checks that are required:
       - `Backend CI / Lint`
       - `Backend CI / Test`
       - `Frontend Tests / Vitest`
       - `Rust CI / Clippy + Tests`
       - `Lighthouse CI / Lighthouse Audit`

### 2. Required Status Checks
Ensure these status checks must pass before merging:
- Backend CI (lint, test, security scan)
- Frontend Tests (unit and E2E)
- Rust CI (clippy, tests, audit)
- Lighthouse CI (performance budget)
- Security Scan (weekly)

### 3. Merge Options
- [ ] Allow squash merging
- [ ] Allow rebase merging
- [ ] Allow merge commits
- [ ] Automatically delete head branches

### 4. Branch Policies
1. **Pull Request Requirements**:
   - [ ] Require linked issues
   - [ ] Require successful builds
   - [ ] Require code review
   - [ ] Limit to users with write access

2. **Work in Progress Limits**:
   - Maximum 3 in-progress PRs per developer

3. **Branch Naming Convention**:
   - Feature branches: `feature/description`
   - Bug fixes: `fix/description`
   - Documentation: `docs/description`
   - Chores: `chore/description`

## Workflow
1. Create a new branch from `dev`
2. Make changes and commit with descriptive messages
3. Push changes and create a PR to `dev`
4. Ensure all CI checks pass
5. Get at least one approval
6. Rebase on latest `dev` if needed
7. Merge using squash and merge

## Code Review Guidelines
- Review should focus on code quality, not just functionality
- All new code must have tests
- Documentation updates required for new features
- Follow the project's coding standards
- Security considerations must be addressed
