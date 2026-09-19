# Rescue Center Management System

A Flask application for tracking donated/purchased items across multiple rescue centers.

## Features
- Multi-center support with user assignments
- Item registration, editing, and decommissioning (no deletion)
- Category and donor organization management
- Item transfers with multi-stage approval workflow:
  1. User at source center submits transfer
  2. Admin approves (or rejects)
  3. Destination center user confirms receipt
- Full audit trail: item status, transfer history, who did what and when
- Admin dashboard for users, centers, categories, organizations

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # then edit SECRET_KEY
python run.py