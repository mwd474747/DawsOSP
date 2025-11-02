# DawsOS Product Specification

## Overview

DawsOS is an AI-powered portfolio management system that provides comprehensive analysis, optimization, and reporting capabilities.

## Core Features

### Portfolio Management
- Real-time portfolio tracking
- Performance analytics
- Risk assessment
- Optimization recommendations

### AI-Powered Analysis
- Macro regime detection
- Scenario analysis
- Risk modeling
- Alert generation

### Reporting & Visualization
- Interactive dashboards
- PDF report generation
- Custom visualizations
- Data export

## Technical Architecture

- **Backend**: FastAPI with PostgreSQL (Python 3.11+)
- **Frontend**: React 18 SPA (`full_ui.html` - single HTML file, no build step)
- **Authentication**: JWT with RBAC
- **Database**: PostgreSQL 14+ with TimescaleDB extension
- **APIs**: RESTful with OpenAPI documentation
- **Deployment**: Replit-first (direct Python execution, no Docker)

## User Roles

- **ADMIN**: Full system access
- **MANAGER**: Portfolio management access
- **USER**: Standard user access
- **VIEWER**: Read-only access

## Security

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection protection
