# DawsOS - AI-Powered Portfolio Management Platform

## Project Overview
DawsOS is an AI-powered portfolio management platform built on pattern-driven agent orchestration. The system provides comprehensive portfolio analytics, risk management, and automated insights through a sophisticated agent architecture.

## Recent Changes (Nov 8, 2025)
- **Completed Phase -1 Database Reconciliation**
  - ✅ Restored missing audit_log table (migration 010)
  - ✅ Fixed holding_deep_dive pattern NoneType errors
  - ✅ Removed broken macro_data_agent import
  - ✅ Simplified authentication (removed unused 761-line auth.py)

## User Preferences
- **Development Priority**: Simplicity and speed over complexity
- **Authentication**: Simple SHA256 for development, defer bcrypt for production
- **Database**: Development database only - no production access
- **Error Handling**: Fix in place rather than rewriting from scratch

## Project Architecture

### Core Components
1. **Pattern System**: 15 orchestrated patterns for portfolio analysis
2. **Agent Runtime**: Financial analyst agent with 30+ capabilities
3. **Dual Architecture**: Monolithic server (combined_server.py) + modular backend
4. **Database**: PostgreSQL with 38 tables, RLS policies

### Authentication System
- **Primary**: `backend/app/auth/dependencies.py` (simple, functional)
- **Removed**: `backend/app/services/auth.py` (complex, unused)
- **Core Pattern**: 48 endpoints use `require_auth` decorator

### Database Status
- **Tables**: 38 active tables
- **Transactions**: 65 records (BUY, SELL, DIVIDEND, TRANSFER_IN)
- **Lots**: 17 open positions
- **Users**: 4 test accounts
- **Audit Log**: Restored and functional

### Known Issues
- All lots are open (none closed) - may need investigation
- Transaction to cash flow mismatch (65 vs 31 records)
- Some patterns return stub data (needs Phase 0 work)

## Phase 0 Planning (Next Steps)
1. **Pattern Testing**: Verify all 15 patterns execute correctly
2. **Stub Data Replacement**: Replace mock data with real computations
3. **Performance Optimization**: Baseline and optimize slow queries
4. **Production Preparation**: Security hardening, bcrypt migration

## Technical Debt
- Dual parallel architecture needs reconciliation
- Authentication complexity can be further reduced
- Pattern definitions need validation and optimization

## Development Guidelines
1. Always check existing code before adding new features
2. Preserve pattern execution flows during refactoring
3. Use simple solutions - avoid over-engineering
4. Test patterns after any database or authentication changes

## Key Files
- `combined_server.py` - Main server entry point
- `backend/app/auth/dependencies.py` - Authentication system
- `backend/app/agents/financial_analyst.py` - Core agent logic
- `migrations/` - Database migration scripts
- `PRODUCTION_ISSUES_ACTION_PLAN.md` - Detailed fix documentation