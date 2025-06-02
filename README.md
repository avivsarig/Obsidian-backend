# Obsidian Task Automation

FastAPI wrapper for automated Obsidian task management with Git-based vault operations.

## Overview

Transforms existing Python automation scripts into a REST API for programmatic task management. Designed to integrate with Obsidian vaults stored in Git repositories.

**Status:** Phase 1 Development - Basic API wrapping of existing automation logic

## Architecture

- **Interactive Operations**: FastAPI on AWS EC2 (this repo)
- **Batch Operations**: GitHub Actions (planned)
- **Storage**: Git-based Obsidian vault with markdown files

## Project Structure

```
app/src/
├── automation/          # Original task automation logic
│   ├── classes.py       # TaskItem, ArchiveItem dataclasses
│   ├── vault_manager.py # File operations for Obsidian vault
│   ├── task_logic.py    # Core task processing functions
│   └── config.yaml      # Automation settings
├── api/routes/v1/       # FastAPI endpoints
├── core/config.py       # API configuration
├── models/              # Pydantic models (TODO)
└── services/            # Business logic layer (TODO)
```

## Setup

### Development

```bash
# Clone and install
git clone <repo-url>
cd obsidian-task-automation
pip install -r requirements-dev.txt

# Run locally (from project root)
uvicorn app.src.main:app --reload

# Or with Python module syntax
python -m app.src.main
```

### Production

```bash
# Deploy infrastructure
cd infrastructure/terraform/environments/prod
terraform init
terraform plan
terraform apply

# TODO: Docker deployment commands
```

## API Endpoints

### Current (Phase 1)
- `GET /health` - Health check
- `POST /api/v1/tasks/process-active` - TODO: Process active tasks
- `POST /api/v1/tasks/process-completed` - TODO: Process completed tasks

### Planned (Phase 2)
- `GET /api/v1/tasks` - List tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `POST /api/v1/tasks` - Create task
- `PUT /api/v1/tasks/{id}` - Update task

## Configuration

### Automation Settings
Edit `app/src/automation/config.yaml`:
```yaml
tasks: "Tasks"
completed_tasks: "Tasks/Completed"
archive: "Knowledge Archive"
retent_for_days: 14
```

### API Settings
Set environment variables:
```bash
VAULT_PATH=/path/to/obsidian/vault
API_KEY=your-secret-key
LOG_LEVEL=INFO
```

## Task Model

```python
@dataclass
class TaskItem:
    title: str
    content: str
    is_project: bool = False
    do_date: str | datetime | None = ""
    due_date: str | datetime | None = ""
    completed_at: str | datetime | None = ""
    done: bool = False
    is_high_priority: bool = False
    repeat_task: Optional[str] = ""
```

## Development Roadmap

- **Phase 1**: Basic API wrapping (current)
- **Phase 2**: Enhanced Pydantic models + file locking
- **Phase 3**: Full service layer + GitHub Actions batch processing
- **Phase 4**: WhatsApp & Google Workspace integrations

## Testing

```bash
# TODO: Run tests
pytest app/tests/

# TODO: Run with coverage
pytest --cov=app/src app/tests/
```

**Status:** No tests implemented yet. Test structure is in place but all test files are empty.

## Infrastructure

AWS deployment via Terraform:
- EC2 instances (t3.micro dev, t3.small prod)
- VPC with public/private subnets
- CloudWatch monitoring
- Cost budgets (~$30/month)

## Contributing

1. Create feature branch
2. Add tests for new functionality
3. Ensure all tests pass
4. Submit PR with clear description

## License

MIT License - see [LICENSE](LICENSE) file for details.
