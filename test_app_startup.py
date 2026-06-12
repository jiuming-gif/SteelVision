import sys
import os
import subprocess

print("Starting startup test...")

def install_package(package):
    try:
        __import__(package)
        print(f"{package} is already installed.")
    except ImportError:
        print(f"{package} not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
            print(f"Successfully installed {package}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            sys.exit(1)

# Ensure core packages are installed
install_package("fastapi")
install_package("uvicorn")
install_package("sqlalchemy")
install_package("pydantic")
install_package("numpy")
install_package("Pillow")
install_package("requests")
install_package("torch")
install_package("python-dotenv")

try:
    from main import app
    print("Successfully imported main.app.")
    from database import engine
    print("Successfully imported database.engine.")
    from models import Base
    print("Successfully imported models.Base.")
    from cv_model_inference import cv_model
    print("Successfully imported cv_model_inference.cv_model.")
    from agent import RepairAgent
    print("Successfully imported agent.RepairAgent.")

    print("All main components imported successfully.")

    # Attempt to create database tables to check SQLAlchemy setup
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created (or already exist).")

    # Check if CV model is loaded
    if cv_model is not None:
        print("CV model loaded successfully.")
    else:
        print("CV model is None, check cv_model_inference.py for errors.")

    # Check if RepairAgent can be instantiated
    try:
        agent = RepairAgent()
        print("RepairAgent instantiated successfully.")
    except Exception as e:
        print(f"Error instantiating RepairAgent: {e}")

    print("App startup check completed successfully!")

except ImportError as e:
    print(f"ImportError: {e}. Check your PYTHONPATH and module names.")
except Exception as e:
    print(f"An unexpected error occurred during startup check: {e}")