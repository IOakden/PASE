#!/usr/bin/env python3
"""
Script to verify PASE environment setup.
"""

import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python version {version.major}.{version.minor}.{version.micro} is too old. Need 3.8+")
        return False


def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {package_name}: Not installed")
        return False


def check_torch_gpu():
    """Check PyTorch GPU availability."""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        elif torch.backends.mps.is_available():
            print("✓ Apple MPS (Metal) available")
        else:
            print("⚠ GPU not available. Will use CPU (slower)")
        return True
    except ImportError:
        print("✗ PyTorch not installed")
        return False


def check_directories():
    """Check if required directories exist."""
    required_dirs = [
        'data/pdb',
        'data/asbench',
        'src',
        'outputs/models',
        'outputs/figures',
        'notebooks'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist


def check_config_files():
    """Check if configuration files exist."""
    config_files = [
        'config.yaml',
        'requirements.txt',
        'setup.py',
        '.gitignore'
    ]
    
    all_exist = True
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ Config file exists: {file_path}")
        else:
            print(f"✗ Config file missing: {file_path}")
            all_exist = False
    
    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("PASE Environment Verification")
    print("=" * 60)
    
    print("\n[1] Checking Python Version...")
    python_ok = check_python_version()
    
    print("\n[2] Checking Core Packages...")
    packages = [
        ('torch', 'torch'),
        ('torch-geometric', 'torch_geometric'),
        ('biopython', 'Bio'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
    ]
    
    packages_ok = all(check_package(name, import_name) for name, import_name in packages)
    
    print("\n[3] Checking GPU Availability...")
    gpu_ok = check_torch_gpu()
    
    print("\n[4] Checking Directory Structure...")
    dirs_ok = check_directories()
    
    print("\n[5] Checking Configuration Files...")
    config_ok = check_config_files()
    
    print("\n" + "=" * 60)
    if all([python_ok, packages_ok, dirs_ok, config_ok]):
        print("✓ All checks passed! Environment is ready.")
        print("\nNext steps:")
        print("  1. Download ASBench dataset to data/asbench/")
        print("  2. Download PDB files to data/pdb/")
        print("  3. Run data exploration: jupyter notebook")
        return 0
    else:
        print("✗ Some checks failed. Please install missing dependencies.")
        print("\nTo install packages:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())

