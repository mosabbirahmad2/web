import os
import sys
import subprocess

def run_command(command):
    """Helper to run django commands since manage.py was removed"""
    # To run migrations, we actually need the manage.py behavior.
    # Since we deleted manage.py, we must use the full path to the app.
    # The most reliable way in this environment is to use 'python manage.py'
    # if it existed, but since it doesn't, we must call the django management command.

    # We create a temporary manage.py just for the migration to work
    with open('manage.py', 'w', encoding='utf-8') as f:
        f.write('''
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)
''')

    full_cmd = ["python", "manage.py"] + command.split()
    try:
        subprocess.run(full_cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Start server
        # For the server, we create manage.py and run it
        with open('manage.py', 'w', encoding='utf-8') as f:
            f.write('''
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)
''')
        subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:5000"])
    else:
        action = sys.argv[1]
        print(f"Executing {action}...")
        # Split the action (e.g., "makemigrations products") into a list
        run_command(f" {action} {' '.join(sys.argv[2:])}")
