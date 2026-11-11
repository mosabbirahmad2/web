import os
import sys
import subprocess

def ensure_manage_py():
    if not os.path.exists('manage.py'):
        with open('manage.py', 'w', encoding='utf-8') as f:
            f.write('''import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)
''')

def run_command(command):
    ensure_manage_py()
    full_cmd = [sys.executable, "manage.py"] + command.split()
    try:
        subprocess.run(full_cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ensure_manage_py()
    if len(sys.argv) == 1:
        try:
            print("Checking and applying database migrations...")
            subprocess.run([sys.executable, "manage.py", "migrate"])
            subprocess.run([sys.executable, "manage.py", "createcachetable"])
            subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:5000"])
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        action = sys.argv[1]
        print(f"Executing: {action}...")
        run_command(f"{action} {' '.join(sys.argv[2:])}")
