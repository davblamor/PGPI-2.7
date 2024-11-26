# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set the working directory to where manage.py is located
WORKDIR /app/backend

# Collect static files for Django
RUN python manage.py collectstatic --noinput

# Expose the port Render dynamically assigns (default is 8000)
EXPOSE 8000

# Start the Django app using the Render-provided PORT environment variable
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
