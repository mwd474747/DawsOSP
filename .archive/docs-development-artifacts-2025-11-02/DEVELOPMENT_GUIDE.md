# DawsOS Development Guide

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+
- Git

### Environment Setup
1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Set up database
5. Configure environment variables

### Running Locally
```bash
# Backend
./backend/run_api.sh

# Frontend
cd dawsos-ui && npm run dev
```

## Code Structure

### Backend
- `app/` - Main application code
- `tests/` - Test files
- `db/` - Database schemas and migrations
- `scripts/` - Utility scripts

### Frontend
- `src/app/` - Next.js app directory
- `src/components/` - React components
- `src/lib/` - Utility functions and API clients
- `src/types/` - TypeScript type definitions

## Development Workflow

1. Create feature branch
2. Implement changes
3. Write tests
4. Run test suite
5. Create pull request
6. Code review
7. Merge to main

## Testing

```bash
# Run all tests
pytest backend/tests/

# Run specific test
pytest backend/tests/test_auth.py

# Run with coverage
pytest --cov=backend backend/tests/
```

## Code Standards

- Follow PEP 8 for Python
- Use TypeScript for frontend
- Write comprehensive tests
- Document public APIs
- Use meaningful commit messages
