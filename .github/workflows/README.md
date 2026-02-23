# GitHub Actions Workflows

This directory contains CI/CD workflows for SOP-Bench.

## Workflows

### 1. Lint (`lint.yml`)

**Triggers**: Push to main/mainline, Pull Requests

**Purpose**: Ensures code quality and consistency

**Checks**:
- Code formatting with Black
- Import sorting with isort
- Linting with Ruff
- Type checking with MyPy (non-blocking)

**Usage**: Runs automatically on every PR. Fix issues locally:
```bash
black src/ tests/
isort src/ tests/
ruff check src/ tests/ --fix
mypy src/
```

### 2. Tests (`test.yml`)

**Triggers**: Push to main/mainline, Pull Requests

**Purpose**: Validates functionality across Python versions

**Tests**:
- Runs pytest on Python 3.9, 3.10, 3.11
- Generates coverage report
- Uploads coverage to Codecov

**Mock AWS**: Uses fake AWS credentials for testing (no real AWS calls)

**Usage**: Runs automatically. Run locally:
```bash
pytest tests/ -v --cov=amazon_sop_bench
```

## Setup Instructions

### For Repository Maintainers

#### 1. Enable GitHub Actions

Actions should be enabled by default. Verify at:
`https://github.com/amazon-science/SOP-Bench/settings/actions`

#### 2. Configure Codecov (Optional)

For coverage reporting:
1. Go to https://codecov.io/
2. Sign in with GitHub
3. Add your repository
4. Copy the upload token
5. Add to GitHub Secrets as `CODECOV_TOKEN` (optional, works without it)

### For Contributors

No setup needed! Workflows run automatically when you:
- Open a pull request
- Push commits to your PR

**Check workflow status**:
- On your PR, scroll to "Checks" section
- Click on failed checks to see details
- Fix issues and push new commits

## Workflow Status Badges

Add these to your README.md:

```markdown
[![Lint](https://github.com/amazon-science/SOP-Bench/actions/workflows/lint.yml/badge.svg)](https://github.com/amazon-science/SOP-Bench/actions/workflows/lint.yml)
[![Tests](https://github.com/amazon-science/SOP-Bench/actions/workflows/test.yml/badge.svg)](https://github.com/amazon-science/SOP-Bench/actions/workflows/test.yml)
```

## Troubleshooting

### Lint Failures

**Black formatting**:
```bash
black src/ tests/
```

**Import sorting**:
```bash
isort src/ tests/
```

**Ruff linting**:
```bash
ruff check src/ tests/ --fix
```

### Test Failures

**Run tests locally**:
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_benchmarks/test_loader.py -v

# With coverage
pytest tests/ --cov=amazon_sop_bench --cov-report=html
```

**Check coverage report**:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Workflow Permissions

Workflows have these permissions:
- **Read**: Repository contents
- **Write**: Pull request comments, checks
- **Secrets**: Access to repository secrets

## Best Practices

1. **Always run tests locally** before pushing
2. **Fix lint issues** before requesting review
3. **Don't commit** if workflows fail
4. **Check workflow logs** for detailed error messages
5. **Keep dependencies updated** in requirements files

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [pytest Documentation](https://docs.pytest.org/)

## Support

For workflow issues:
- Check workflow logs in Actions tab
- Review this README
- Open an issue with workflow run link
- Open an issue on the [GitHub repository](https://github.com/amazon-science/sop-bench/issues)
