"""
Setup check script for SkyHustle.
This script checks if all required dependencies are installed and environment variables are set.
"""
import importlib
import os
import sys

def check_dependency(package_name, min_version=None):
    """Check if a dependency is installed."""
    try:
        # Try to import the package
        module = importlib.import_module(package_name)
        
        # If a minimum version is specified, check it
        if min_version:
            version = getattr(module, '__version__', None)
            if version and version < min_version:
                print(f"❌ {package_name} version {version} is installed, but version {min_version} or later is required")
                return False
        
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is not installed")
        return False

def check_env_variable(var_name):
    """Check if an environment variable is set."""
    value = os.environ.get(var_name)
    if value:
        masked_value = value[:3] + '*' * (len(value) - 6) + value[-3:] if len(value) > 6 else '******'
        print(f"✅ {var_name} is set: {masked_value}")
        return True
    else:
        print(f"❌ {var_name} is not set")
        return False

def main():
    """Run all checks."""
    print("Running SkyHustle setup checks...\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 11:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} is installed")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} is installed, but version 3.11 or later is required")
    
    # Check dependencies
    dependencies = [
        "flask",
        "telegram",
        "gspread",
        "oauth2client",
        "dotenv",
        "gunicorn",
    ]
    
    all_deps_installed = all(check_dependency(dep) for dep in dependencies)
    
    # Check environment variables
    required_env_vars = [
        "BOT_TOKEN",
        "BASE64_CREDS",
        "SHEET_ID",
        "SESSION_SECRET"
    ]
    
    all_env_vars_set = all(check_env_variable(var) for var in required_env_vars)
    
    # Summary
    print("\nSetup check summary:")
    if all_deps_installed:
        print("✅ All required dependencies are installed")
    else:
        print("❌ Some dependencies are missing. Please install them using:")
        print("   pip install -r requirements.txt")
    
    if all_env_vars_set:
        print("✅ All required environment variables are set")
    else:
        print("❌ Some environment variables are missing. Please set them before running the bot.")
        print("   You can create a .env file with these variables for development.")
    
    if all_deps_installed and all_env_vars_set:
        print("\n✅ All checks passed! You can run the bot with:")
        print("   python main.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues before running the bot.")

if __name__ == "__main__":
    main()