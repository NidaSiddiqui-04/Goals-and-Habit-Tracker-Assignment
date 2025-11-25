Write-Output "Starting build script (PowerShell)"

Write-Output "Installing dependencies"
pip install -r requirements.txt

Write-Output "Running migrations (optional)"
python manage.py makemigrations --noinput
python manage.py migrate --noinput

Write-Output "Collecting static files"
python manage.py collectstatic --noinput

Write-Output "Build script complete"
