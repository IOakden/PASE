# Allosteric Site Prediction using GVP-GNN

## Overview

This project predicts allosteric sites on proteins using a Graph-based Geometric Vector Perceptron Graph Neural Network (GVP-GNN). The pipeline uses 3D protein structures (from PDB files) and confirmed allosteric site annotations (from ASBench) to train a model that identifies potential allosteric residues in any protein.

## Motivation

Allosteric sites regulate protein activity by binding modulators at locations distinct from the active site. Predicting these sites computationally can accelerate drug discovery and deepen our understanding of protein regulation.

## Datasets

### 1. ASBench Core Set

- **Content**: 320 confirmed allosteric proteins with annotated residues.
- **Format**: XLS file (`ASBench_Core_Set.xls`) with columns:
  - Allosteric Site
  - PDB ID
  - Protein Name
  - Chain ID
  - Residue ID (PDB) (core for labeling)
- **Usage**: Used to generate labels for training (residues part of an allosteric site vs non-allosteric).

### 2. Protein Data Bank (PDB)

- **Content**: Full 3D structures of proteins (any chain/residue).
- **Format**: `.pdb` files containing ATOM entries with residue, chain, and atomic coordinates.
- **Usage**: Provides 3D geometric and chemical features for input to GVP-GNN.

## Data Processing Pipeline

### 1. PDB Parsing

Read `.pdb` files line by line.

Extract:
- Atom coordinates (x, y, z)
- Residue name and number
- Chain ID
- Atom type/element

### 2. Residue Mapping

Match Chain ID + Residue ID from PDB to ASBench annotations.

Label atoms/residues as:
- `1` → part of an allosteric site
- `0` → non-allosteric

### 3. Graph Construction

**Nodes**: residues or atoms (atom-level recommended for fine-grained geometric modeling)

**Node features**:
- Chemical type (one-hot encoding)
- Backbone atom coordinates (N, Cα, C, O)
- Side-chain geometric features (optional)

**Edges**:
- Distance-based connectivity (e.g., edges between nodes < 8 Å apart)
- Optional: covalent bond information

**Edge features**:
- Euclidean distance
- Direction vector (unit vector between nodes)

### 4. Input to GVP-GNN

- **Node features**: scalar + vector embeddings
- **Edge features**: scalar + vector embeddings
- **Labels**: atom/residue-level allosteric site labels

## Model Architecture

### 1. GVP-GNN Layers

**Geometric Vector Perceptron (GVP)**:
- Processes scalar and vector features jointly
- Preserves geometric equivariance

**Message Passing**:
- Aggregate features from neighboring nodes
- Update node embeddings with GVP layers

**Output**:
- Atom/residue embeddings
- Probability of being part of an allosteric site

### 2. Output Layer

- Sigmoid activation for binary classification (allosteric vs non-allosteric)
- Optionally aggregate atom predictions to residue-level predictions

## Training

### Data Splits

- **Train**: ~70% proteins
- **Validation**: ~15% proteins
- **Test**: ~15% proteins

> **Note**: Split by protein to avoid leakage.

### Loss Function

Binary Cross-Entropy at atom/residue level

### Metrics

- Precision, Recall, F1-score (residue-level)
- ROC-AUC for probability scores
- Optional: Top-N residue accuracy for practical drug discovery

### Training Tips

- Atom-level GVP-GNN may require significant GPU memory
- Use gradient accumulation or batch subgraphs if full protein graphs are too large
- Data augmentation: slight perturbation of atomic coordinates

## Inference

**Input**: PDB of any protein

**Output**:
- Atom/residue-level probability of being an allosteric site
- Highlight predicted allosteric residues in 3D visualizations (PyMOL, NGLViewer, or ChimeraX)

## Visualization

Render protein structures with predicted allosteric sites:
- Color-coded residues (e.g., red = high probability, gray = low)

Optional interactive 3D visualization:
- **NGLViewer** for web
- **PyMOL/ChimeraX** for desktop

## Directory Structure

```
project/
│
├─ data/
│  ├─ pdb/                   # Downloaded PDB files
│  └─ asbench/               # ASBench Core Set XLS
│
├─ src/
│  ├─ preprocessing.py       # PDB parsing & labeling
│  ├─ graph_builder.py       # Construct graphs for GVP
│  ├─ gvp_model.py           # GVP-GNN implementation
│  ├─ train.py               # Training loop
│  ├─ inference.py           # Predicting new proteins
│  └─ visualization.py       # Render predictions in 3D
│
├─ outputs/
│  ├─ models/                # Trained models
│  └─ figures/               # 3D visualizations
│
└─ README.md
```

## Dependencies

- PyTorch ≥ 2.0
- PyTorch Geometric + GVP modules
- Biopython (PDB parsing)
- NumPy, Pandas
- NGLViewer / PyMOL (visualization)
- Optional: RDKit (chemical features for side chains)

## Next Steps

1. Implement PDB parsing and residue-label mapping.
2. Construct atom-level graphs for all proteins in ASBench.
3. Implement GVP-GNN with scalar/vector features.
4. Train on ASBench dataset.
5. Evaluate and visualize predictions.
6. Optionally fine-tune on additional PDB proteins without labels using semi-supervised or self-supervised methods.
