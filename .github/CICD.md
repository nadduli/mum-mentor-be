# CI/CD Pipeline Documentation

This document describes the continuous integration and deployment setup for the Mum Mentor Backend API project.

## Overview

The CI/CD pipeline consists of GitHub Actions workflows that ensure code quality, security, and streamlined deployment processes for the Python FastAPI backend.

## Workflows

### 1. CI/CD Pipeline (`deploy.yml`)

**Triggers:**

- Push to `main` or `staging` branches
- Pull requests targeting `main` or `staging` branches
- Manual trigger via `workflow_dispatch` with environment selection

**Jobs:**

- **Run Tests**: Executes code quality checks and tests
  - Set up Python 3.12 environment
  - Install dependencies from requirements.txt
  - Run flake8 linting for code quality
  - Execute pytest test suite
  - Cache pip dependencies for faster builds

- **Deploy to Staging (Auto)**: Automatic deployment to staging environment
  - Triggers on push to `staging` branch
  - Uses password-based SSH authentication
  - Deploys to `/var/www/mum-mentor-be-staging`
  - Runs database migrations with Alembic
  - Restarts systemd service `mum-mentor-api-staging`

- **Deploy to Production (Manual)**: Manual deployment to production
  - Requires manual trigger with `production` target
  - Protected by GitHub environment rules
  - Deploys to `/var/www/mum-mentor-be`
  - Runs database migrations with Alembic
  - Restarts systemd service `mum-mentor-api`

**Status:** ✅ Active

---

## Branch Protection Rules

To maximize the effectiveness of these workflows, configure the following branch protection rules:

### For `main` branch:

1. Require pull request reviews before merging
2. Require status checks to pass:
   - `Run Tests` (from CI/CD workflow)
3. Require conversation resolution before merging
4. Require linear history
5. Include administrators

### For `staging` branch:

1. Require status checks to pass:
   - `Run Tests` (from CI/CD workflow)
2. Require pull request reviews (optional, but recommended)

**How to set up:**

1. Go to repository Settings → Branches
2. Add branch protection rule for `main` and `staging`
3. Configure the requirements listed above

---

## Secrets Configuration

The following secrets need to be configured in GitHub Settings → Secrets and variables → Actions:

### Required for Deployment:

**Server Access:**

- `SERVER_HOST`: Server hostname/IP address
- `SERVER_USER`: SSH username for server access
- `SERVER_PASSWORD`: SSH password for authentication

### Environment Configuration:

**Staging Environment:**
- Environment name: `staging`
- Deployment URL: Server staging endpoint

**Production Environment:**
- Environment name: `production`
- Deployment URL: Server production endpoint
- Required reviewers: Configure team members who must approve production deployments

---

## Local Development

Ensure code quality before pushing by running these commands locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
pytest -v

# Run database migrations (if needed)
alembic upgrade heads
```

---

## Deployment Process

### Staging Deployment (Automatic)

1. Push changes to `staging` branch
2. CI/CD pipeline automatically runs tests
3. If tests pass, deployment to staging server begins
4. Application is updated and restarted
5. Health check verifies deployment success

### Production Deployment (Manual)

1. Ensure all changes are tested in staging
2. Go to GitHub Actions → CI/CD Pipeline
3. Click "Run workflow"
4. Select `production` as target environment
5. Deployment requires approval from configured reviewers
6. Application is updated and restarted on production server

---

## Server Configuration

### Directory Structure:

**Staging:**
- Application path: `/var/www/mum-mentor-be-staging`
- Service name: `mum-mentor-api-staging`
- Python virtual environment: `venv/`

**Production:**
- Application path: `/var/www/mum-mentor-be`
- Service name: `mum-mentor-api`
- Python virtual environment: `venv/`

### Database Migrations:

- Uses Alembic for database schema management
- Staging: Stamps to revision `21c4c314e650` then upgrades
- Production: Runs `alembic upgrade heads`

---

## Troubleshooting

### CI Workflow Fails

1. **Linting errors**: Run `flake8` locally and fix code style issues
2. **Test failures**: Run `pytest -v` locally to identify failing tests
3. **Dependency issues**: Verify `requirements.txt` is up to date
4. **Python version**: Ensure local Python version matches CI (3.12)

### Deployment Fails

1. **SSH Connection**: Verify server credentials in GitHub secrets
2. **Service restart**: Check systemd service status on server
3. **Database migrations**: Review Alembic migration logs
4. **Dependencies**: Ensure all required packages are in requirements.txt

### Database Issues

1. **Migration conflicts**: Review and resolve Alembic migration conflicts
2. **Connection errors**: Verify database configuration and credentials
3. **Schema changes**: Ensure migrations are properly created and tested

---

## Best Practices

1. **Always create feature branches** from `staging`
2. **Write comprehensive tests** for new features and bug fixes
3. **Follow PEP 8** coding standards for Python code
4. **Test database migrations** in staging before production
5. **Monitor application logs** after deployments
6. **Keep dependencies updated** to avoid security vulnerabilities
7. **Use descriptive commit messages** following conventional commit format

---

## Monitoring & Maintenance

- Review failed workflows weekly
- Update GitHub Actions versions quarterly
- Monitor server resources and application performance
- Keep Python and package versions updated
- Review and update deployment configuration as needed
- Monitor database performance and optimize queries

---

## Support

For issues with CI/CD:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Check server logs via SSH
4. Contact the DevOps team or project maintainers
5. Open an issue in the repository

---

**Last Updated:** 2025-01-16
**Maintained By:** Team Kaizen - DevOps Team

<!-- Backend API CI/CD Documentation -->