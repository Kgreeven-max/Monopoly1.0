# Pi-nopoly Setup Instructions

This document explains how to set up both the frontend and backend development environments for Pi-nopoly.

## Prerequisites

### For Backend Development
- Python 3.9 or higher
- pip (Python package manager)

### For Frontend Development
- Node.js 16.x or higher 
- npm (Node.js package manager)

## Setup Scripts

Pi-nopoly provides three setup scripts to help you get started:

1. `setup_python_backend.py` - Sets up the Python backend environment
2. `setup_frontend.py` - Sets up the Node.js frontend environment
3. `make_setup_scripts_executable.py` - Makes the setup scripts executable on Unix/Linux systems

## Step-by-Step Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/pi-nopoly.git
cd pi-nopoly
```

### 2. Make Setup Scripts Executable (Unix/Linux Only)

On Unix/Linux systems, you'll need to make the setup scripts executable:

```bash
python make_setup_scripts_executable.py
```

### 3. Set Up the Backend Environment

The backend setup script will:
- Check your Python version
- Create a virtual environment
- Set up environment variables
- Install dependencies
- Check and create the database

```bash
# On Windows
python setup_python_backend.py

# On Unix/Linux
./setup_python_backend.py
```

If prompted to activate the virtual environment, use:

```bash
# On Windows
venv\Scripts\activate

# On Unix/Linux
source venv/bin/activate
```

Then run the script again to complete the setup.

### 4. Set Up the Frontend Environment

The frontend setup script will:
- Check your Node.js and npm versions
- Create environment files
- Install dependencies
- Verify the Vite configuration

```bash
# On Windows
python setup_frontend.py

# On Unix/Linux
./setup_frontend.py
```

## Running the Application

### Backend

With the virtual environment activated:

```bash
python app.py
```

### Frontend

```bash
cd client
npm run dev
```

The frontend will be available at: http://localhost:3000
The backend API will be available at: http://localhost:5000/api

## Troubleshooting

### Python Virtual Environment Issues

If you have trouble with the virtual environment:

```bash
# Remove the existing virtual environment
rm -rf venv  # Unix/Linux
# Or
rmdir /s /q venv  # Windows

# Create a new one manually
python -m venv venv
```

### Dependency Installation Problems

If certain packages fail to install, try installing them individually:

```bash
pip install package-name
```

### Windows PowerShell Execution Policy

If you get execution policy errors on Windows, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Node.js or npm Issues

If you encounter Node.js or npm issues, ensure you have the correct versions:

```bash
node --version  # Should be 16.x or higher
npm --version   # Should be 6.x or higher
```

If necessary, update Node.js by downloading the latest LTS version from the [official website](https://nodejs.org/).

## Additional Information

For more details about the application, refer to the main README.md file in the project root. 