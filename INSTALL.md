# Installation Guide for PASE

This guide will help you set up the development environment for the PASE (Protein Allosteric Site Predictor) project.

## Prerequisites

- Python 3.8 or higher
- CUDA-capable GPU (recommended, but CPU mode is supported)
- Git

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PASE
```

## Step 2: Create Virtual Environment

### Using venv (recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Using conda (alternative)

```bash
# Create conda environment
conda create -n pase python=3.10
conda activate pase
```

## Step 3: Install PyTorch

Visit [PyTorch's official website](https://pytorch.org/get-started/locally/) to get the installation command for your system.

### For CUDA 11.8 (most common):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### For CUDA 12.1:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### For CPU only (macOS or no GPU):
```bash
pip install torch torchvision torchaudio
```

### For Apple Silicon (M1/M2):
```bash
pip install torch torchvision torchaudio
```

## Step 4: Install PyTorch Geometric

```bash
pip install torch-geometric
pip install pyg-lib torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
```

**Note**: Replace `cu118` with your CUDA version or `cpu` if not using GPU.

## Step 5: Install Other Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Install PASE Package in Development Mode

```bash
pip install -e .
```

This allows you to edit the source code without reinstalling.

## Step 7: Verify Installation

Run this Python script to verify everything is installed correctly:

```bash
python -c "
import torch
import torch_geometric
import Bio
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('PyTorch Geometric version:', torch_geometric.__version__)
print('Biopython installed successfully')
print('✓ Installation successful!')
"
```

## Step 8: Set Up Jupyter (Optional)

If you want to use Jupyter notebooks:

```bash
pip install jupyter ipykernel
python -m ipykernel install --user --name=pase --display-name "Python (PASE)"
```

## Troubleshooting

### Issue: PyTorch Geometric installation fails

**Solution**: Make sure your PyTorch version matches the PyG installation. Check:
```bash
python -c "import torch; print(torch.__version__)"
```
Then use the corresponding PyG wheel URL.

### Issue: CUDA out of memory during training

**Solution**: 
- Reduce batch size in `config.yaml`
- Use gradient accumulation
- Use mixed precision training (enabled by default)

### Issue: Biopython PDB parser warnings

**Solution**: These are usually non-critical. Check the specific warning and refer to Biopython documentation.

### Issue: Import errors

**Solution**: Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
```

## Directory Structure After Setup

```
PASE/
├── data/
│   ├── pdb/                 # PDB files (download separately)
│   ├── asbench/             # ASBench dataset (download separately)
│   └── processed/           # Processed graphs (generated)
├── src/
│   ├── __init__.py
│   └── config.py
├── outputs/
│   ├── models/              # Saved model checkpoints
│   └── figures/             # Visualizations
├── logs/                    # Training logs
├── notebooks/               # Jupyter notebooks
├── config.yaml              # Main configuration
├── requirements.txt
├── setup.py
└── README.md
```

## Next Steps

After installation:

1. Download the ASBench dataset (see Phase 1.2 in ROADMAP.md)
2. Download PDB files for the proteins in ASBench
3. Run data exploration notebooks
4. Start with preprocessing pipeline

## GPU Configuration

Check your GPU status:
```bash
nvidia-smi
```

Configure GPU in `config.yaml`:
```yaml
hardware:
  device: "cuda"  # or "cpu" or "mps" for Apple Silicon
```

## Support

If you encounter issues not covered here, please:
1. Check the ROADMAP.md for detailed instructions
2. Review PyTorch Geometric documentation
3. Open an issue on GitHub (if applicable)

Happy coding! 🚀

