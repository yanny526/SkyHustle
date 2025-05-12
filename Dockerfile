FROM python:3.11-slim

WORKDIR /app

# Copy the requirements first to leverage Docker cache
COPY pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . /app/

# Create a .env file on build (for testing only, in production use environment variables)
RUN touch .env

# Set environment variables (these will be overridden in production with real values)
ENV BOT_TOKEN=your_bot_token_here
ENV BASE64_CREDS=your_base64_creds_here
ENV SHEET_ID=your_sheet_id_here
ENV SESSION_SECRET=your_session_secret_here

# Expose port for web dashboard
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]