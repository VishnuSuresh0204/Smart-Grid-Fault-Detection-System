# Smart Grid Fault Detection System

## Setup

Requires Python 3.11 or later.

1. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Set `DJANGO_SECRET_KEY` to a long, random value. For a local PowerShell
   session, for example:

   ```powershell
   $env:DJANGO_SECRET_KEY = "replace-with-a-long-random-secret"
   ```

   `.env.example` documents the required variable; Django does not load `.env`
   files automatically.

3. Apply migrations and start the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

The local SQLite database, virtual environments, and generated files are
excluded from version control.
