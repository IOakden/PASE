# Project Roadmap: Allosteric Site Prediction using GVP-GNN

## Overview

This roadmap outlines the step-by-step development process for building a machine learning model to predict allosteric binding sites in proteins. Each phase includes key considerations, potential pitfalls, and success criteria.

---

## Phase 1: Project Setup & Data Acquisition

### 1.1 Environment Setup
- [ ] Create Python virtual environment (Python 3.8+)
- [ ] Install core dependencies:
  - PyTorch ≥ 2.0 with CUDA support
  - PyTorch Geometric
  - Biopython for PDB parsing
  - pandas, numpy, scikit-learn
  - matplotlib, seaborn for visualization
- [ ] Create project directory structure
- [ ] Initialize git repository with proper `.gitignore`
- [ ] Set up logging and configuration management

### 1.2 Data Acquisition
- [ ] Download ASBench Core Set dataset
  - Verify: 320 proteins with allosteric annotations
  - Parse XLS to extract: PDB ID, Chain ID, Residue IDs, Allosteric Site annotations
- [ ] Download PDB structures for all ASBench proteins
  - Use Biopython's PDB downloader or RCSB bulk download
  - Verify structure quality (resolution, missing residues)
- [ ] **Optional**: Download active site annotations (from CATALYTIC SITE ATLAS or PDBbind)
  - Critical for defining high-quality negative examples

**Success Criteria**: All 320 proteins downloaded with metadata organized in a database/CSV.

---

## Phase 2: Data Exploration & Quality Assessment

### 2.1 Exploratory Data Analysis
- [ ] **Analyze class distribution**:
  - Count allosteric residues vs total residues per protein
  - Expected severe class imbalance (~1-5% allosteric residues)
  - Visualize distribution across protein families
- [ ] **Protein structure quality checks**:
  - Resolution distribution
  - Missing residues/chains
  - Multi-chain complexes vs monomers
- [ ] **Spatial analysis**:
  - Are allosteric sites primarily surface-exposed or buried?
  - Distance distribution between allosteric sites and active sites
  - Clustering patterns of allosteric residues

### 2.2 Data Quality Issues to Address
- [ ] Handle missing residues in PDB files
- [ ] Resolve annotation mismatches (ASBench IDs may not align with PDB numbering)
- [ ] Deal with multiple chains/biological assemblies
- [ ] Identify and handle protein mutations/variants

**Success Criteria**: Documented data quality report with statistics and visualizations. Clear understanding of class imbalance and spatial properties.

---

## Phase 3: Data Preprocessing & Labeling Strategy

### 3.1 PDB Parsing (`preprocessing.py`)
- [ ] Parse PDB files to extract:
  - Atom coordinates (x, y, z)
  - Residue name, number, and chain ID
  - Atom types and elements
  - B-factors (thermal motion indicators)
  - Secondary structure (via DSSP if needed)
- [ ] Compute per-residue features:
  - Solvent accessible surface area (SASA)
  - Depth (distance from surface)
  - Conservation scores (if MSA available)
  - Physicochemical properties

### 3.2 Label Generation Strategy ⚠️ CRITICAL

**Positive Examples (Allosteric Residues)**:
- [ ] Extract residue IDs from ASBench annotations
- [ ] Map ASBench residue IDs to PDB residue numbering
- [ ] Validate spatial clustering (allosteric residues should be spatially proximal)
- [ ] Label = 1

**Negative Examples (Non-Allosteric Residues)**:
This requires careful consideration to avoid false negatives and create meaningful negatives.

- [ ] **Exclude known active sites**:
  - Use CATALYTIC SITE ATLAS or literature annotations
  - Active sites are functionally distinct from random surface patches
- [ ] **Exclude residues near allosteric sites**:
  - Remove residues within 8-10 Å of any allosteric residue
  - Prevents label noise at allosteric site boundaries
- [ ] **Stratified negative sampling**:
  - Sample negatives proportionally from:
    - Surface-exposed residues (high SASA)
    - Buried residues (low SASA)
    - Different secondary structures (helix, sheet, loop)
  - Prevents model from learning trivial surface vs buried distinction
- [ ] **Class balancing strategy**:
  - Option A: Undersample negatives (e.g., 1:3 or 1:5 ratio)
  - Option B: Use weighted loss function
  - Option C: Use focal loss for hard example mining
- [ ] Label = 0

**Success Criteria**: Balanced dataset with well-defined positive and negative examples. Documentation of negative sampling rationale.

---

## Phase 4: Graph Construction for GVP

### 4.1 Graph Representation (`graph_builder.py`)

**Node Definition**:
- [ ] **Decision**: Atom-level vs Residue-level graphs
  - Atom-level: More detailed but computationally expensive
  - Residue-level: Use Cα or center of mass as node position
  - **Recommendation**: Start with residue-level, then try atom-level

**Node Features**:
- [ ] **Scalar features** (invariant to rotation):
  - Residue type (20 amino acids, one-hot encoded)
  - SASA (solvent accessibility)
  - Depth from surface
  - B-factor (flexibility)
  - Secondary structure (helix/sheet/loop)
- [ ] **Vector features** (equivariant to rotation):
  - Backbone orientation vectors (N→Cα, Cα→C)
  - Normal vector to local surface
  - Direction to center of mass

**Edge Construction**:
- [ ] Distance-based connectivity:
  - **K-nearest neighbors** (e.g., K=10) OR
  - **Distance threshold** (e.g., < 10 Å between Cα atoms)
  - Recommendation: Use KNN for consistent graph structure
- [ ] Compute edge features:
  - Euclidean distance (scalar)
  - Unit direction vector (vector feature)
  - Optionally: dihedral angles, edge type (covalent/non-covalent)

**Graph-level Considerations**:
- [ ] Handle disconnected components (inter-chain contacts)
- [ ] Normalize node positions (center at origin)
- [ ] Data augmentation: random rotations/translations during training

### 4.2 Data Validation
- [ ] Visualize sample graphs (node degrees, edge distributions)
- [ ] Check for isolated nodes
- [ ] Verify GVP feature dimensions (scalar vs vector)
- [ ] Test batch processing with PyTorch Geometric `DataLoader`

**Success Criteria**: Clean graph dataset saved in PyTorch Geometric format with documented feature dimensions.

---

## Phase 5: Baseline Models

### 5.1 Simple Baselines (Establish Lower Bounds)
Before jumping to GVP-GNN, establish baselines:

- [ ] **Random predictor**: Random assignment (should give ~1-5% precision)
- [ ] **Sequence-based logistic regression**:
  - Features: residue type, position, sequence context
  - Establishes if sequence alone is predictive
- [ ] **Structure-based random forest**:
  - Features: SASA, depth, B-factor, secondary structure
  - Tests if hand-crafted features capture signal
- [ ] **Simple GNN** (e.g., GCN or GAT):
  - Use only scalar features (no geometric vectors)
  - Tests if graph structure helps without geometric information

**Success Criteria**: Baseline results documented. Understanding of which features are most predictive.

---

## Phase 6: GVP-GNN Implementation

### 6.1 Model Architecture (`gvp_model.py`)

**Use Existing Implementation**:
- [ ] Use [drorlab/gvp-pytorch](https://github.com/drorlab/gvp-pytorch) or PyG implementation
- [ ] Adapt for node classification (not graph classification)

**Architecture Components**:
- [ ] **Input embedding layer**:
  - Project raw features to GVP hidden dimensions
  - Example: (scalar_dim=20, vector_dim=3) → (128, 16)
- [ ] **GVP-GNN layers** (3-5 layers):
  - Message passing with geometric vector features
  - Residual connections
  - Layer normalization
- [ ] **Output head**:
  - Pool GVP features to scalar
  - 2-layer MLP
  - Sigmoid activation for binary classification
- [ ] **Loss function**:
  - Binary cross-entropy with class weights OR
  - Focal loss to handle class imbalance

### 6.2 Model Configuration
- [ ] Hyperparameter search space:
  - Number of GVP layers: [3, 4, 5]
  - Hidden dimensions: [(128, 16), (256, 32)]
  - Dropout: [0.1, 0.2, 0.3]
  - Learning rate: [1e-4, 5e-4, 1e-3]
  - KNN value: [10, 15, 20]
- [ ] Regularization:
  - Dropout in MLP layers
  - Weight decay
  - Optional: graph dropout (edge dropout)

**Success Criteria**: Working GVP-GNN model that can forward pass a batch of protein graphs.

---

## Phase 7: Training Pipeline

### 7.1 Data Splitting Strategy
- [ ] **Protein-level splits** (critical to avoid data leakage):
  - Train: 70% of proteins (~224 proteins)
  - Validation: 15% (~48 proteins)
  - Test: 15% (~48 proteins)
- [ ] **Stratify by**:
  - Protein family (avoid related proteins in different splits)
  - Size (balance small and large proteins)
- [ ] Consider sequence similarity clustering (e.g., CD-HIT at 30% identity)

### 7.2 Training Loop (`train.py`)
- [ ] Implement training loop:
  - Mini-batch training (may need to batch by number of nodes, not graphs)
  - Gradient accumulation if memory-limited
  - Mixed precision training (FP16) for efficiency
- [ ] Optimizer: Adam with learning rate scheduling
  - Warmup for first few epochs
  - ReduceLROnPlateau or cosine annealing
- [ ] Early stopping based on validation F1-score
- [ ] Checkpointing (save best model on validation set)
- [ ] Logging:
  - TensorBoard or Weights & Biases
  - Track loss, precision, recall, F1, AUROC per epoch

### 7.3 Handling Class Imbalance
- [ ] Option 1: Weighted loss (weight inversely proportional to class frequency)
- [ ] Option 2: Focal loss (focus on hard examples)
- [ ] Option 3: Oversample positive class (duplicate graphs with allosteric sites)
- [ ] **Recommendation**: Start with weighted loss, experiment with focal loss

**Success Criteria**: Model trains without errors, converges on training set, generalizes to validation set.

---

## Phase 8: Evaluation & Analysis

### 8.1 Quantitative Metrics
Evaluate on the held-out test set:

- [ ] **Threshold-based metrics** (at optimal threshold):
  - Precision, Recall, F1-score
  - Confusion matrix
- [ ] **Threshold-independent metrics**:
  - ROC-AUC
  - Precision-Recall AUC (better for imbalanced data)
- [ ] **Ranking metrics**:
  - Top-K accuracy (K=5, 10, 20 residues)
  - Mean Average Precision
  - Critical for drug discovery: "Are the top predictions correct?"
- [ ] **Per-protein analysis**:
  - F1-score per protein
  - Identify failure cases

### 8.2 Ablation Studies
Understand what contributes to model performance:

- [ ] Remove vector features (scalar-only GNN)
- [ ] Remove geometric information (shuffle node positions)
- [ ] Use different edge construction strategies
- [ ] Use different node features (SASA, depth, etc.)
- [ ] Vary number of GVP layers

### 8.3 Error Analysis
- [ ] Analyze false positives:
  - Are they near allosteric sites?
  - Are they structurally similar to allosteric sites?
  - Are they active sites mislabeled as negative?
- [ ] Analyze false negatives:
  - Are they on protein surface or buried?
  - Are they poorly annotated in ASBench?
  - Do they have unusual amino acid composition?

### 8.4 Biological Validation
- [ ] Compare predictions to literature (case studies on well-known proteins)
- [ ] Check if predicted sites have known regulatory function
- [ ] Visualize predictions on 3D structures (PyMOL/ChimeraX)
- [ ] Compute enrichment of predicted sites in:
  - Protein-protein interfaces
  - Flexible regions (high B-factors)
  - Evolutionary conserved patches

**Success Criteria**: Test set F1 > 0.4 (reasonable given class imbalance), Top-10 precision > 0.3, clear understanding of model strengths/weaknesses.

---

## Phase 9: Inference & Visualization

### 9.1 Inference Pipeline (`inference.py`)
- [ ] Input: Any PDB file
- [ ] Pipeline:
  1. Parse PDB
  2. Compute features
  3. Build graph
  4. Run model inference
  5. Output: per-residue allosteric probability
- [ ] Handle edge cases:
  - Missing residues
  - Non-standard amino acids
  - Multi-chain complexes
- [ ] Batch processing for multiple proteins

### 9.2 Visualization (`visualization.py`)
- [ ] **3D structure rendering**:
  - Color residues by predicted probability (blue → red gradient)
  - Highlight top-K predictions
- [ ] **Integration with molecular viewers**:
  - PyMOL script generation
  - ChimeraX attribute file
  - NGLViewer for web (interactive Jupyter widget)
- [ ] **Summary plots**:
  - Per-residue probability histogram
  - Spatial distribution on protein surface
  - Predicted allosteric sites overlaid on secondary structure

**Success Criteria**: Easy-to-use inference script that outputs publication-quality visualizations.

---

## Phase 10: Model Interpretability

### 10.1 Attention Analysis
- [ ] If using attention mechanisms:
  - Visualize attention weights between residues
  - Identify which neighbors influence allosteric predictions
- [ ] GNNExplainer or similar tools:
  - Extract important subgraphs for each prediction
  - Understand local structural motifs

### 10.2 Feature Importance
- [ ] Gradient-based attribution (integrated gradients)
- [ ] Permutation importance for node features
- [ ] Analyze learned embeddings (t-SNE/UMAP)

**Success Criteria**: Interpretable explanations that align with biological knowledge.

---

## Phase 11: Advanced Improvements (Optional)

### 11.1 Data Augmentation
- [ ] Increase training data:
  - AlphaFold-predicted structures (if experimental PDBs insufficient)
  - Homology models for related proteins
- [ ] Weak supervision:
  - Proteins with known allosteric modulators (but no residue annotations)
  - Use binding pocket detection tools as pseudo-labels

### 11.2 Semi-Supervised Learning
- [ ] Pre-train on large unlabeled PDB:
  - Self-supervised tasks: masked residue prediction, distance prediction
  - Transfer learning from structure prediction models
- [ ] Fine-tune on ASBench allosteric data

### 11.3 Multi-Task Learning
- [ ] Jointly predict:
  - Allosteric sites
  - Active sites
  - Protein-protein interfaces
  - Binding pockets
- [ ] Shared encoder, task-specific heads
- [ ] May improve feature learning

### 11.4 Ensemble Models
- [ ] Train multiple models with different:
  - Random seeds
  - Architectures (GVP, E(3)-equivariant, Transformer)
  - Feature sets
- [ ] Ensemble via averaging or stacking

**Success Criteria**: Improved performance over baseline GVP-GNN.

---

## Phase 12: Documentation & Deployment

### 12.1 Code Documentation
- [ ] Docstrings for all functions/classes
- [ ] Type hints throughout codebase
- [ ] Example notebooks for each module
- [ ] Update README with installation and usage instructions

### 12.2 Model Release
- [ ] Save trained model weights
- [ ] Document hyperparameters and training details
- [ ] Create inference API (Flask/FastAPI web server)
- [ ] Docker container for reproducibility

### 12.3 Paper/Report
- [ ] Write up methodology
- [ ] Compare to existing methods (PAIRpred, Allosite, PASSerRank)
- [ ] Benchmark results
- [ ] Case studies on novel proteins

**Success Criteria**: Reproducible research artifact with clear documentation.

---

## Key Risks & Mitigation Strategies

| Risk | Mitigation |
|------|------------|
| **Severe class imbalance** | Use focal loss, stratified negative sampling, evaluate with AUPRC |
| **Limited training data (320 proteins)** | Pre-train on unlabeled PDB, data augmentation, avoid overfitting |
| **Annotation quality issues** | Manual validation of subset, exclude low-confidence annotations |
| **GPU memory constraints** | Use gradient accumulation, smaller batch sizes, residue-level graphs |
| **Model doesn't learn** | Start with simpler baselines, ablation studies, check for bugs in graph construction |
| **Predictions not interpretable** | Use attention mechanisms, GNNExplainer, compare to structural biology literature |

---

## Success Metrics by Phase

| Phase | Key Metric | Target |
|-------|------------|--------|
| Phase 2 | Data quality report completed | 100% |
| Phase 4 | Graphs constructed for all proteins | 100% |
| Phase 5 | Baseline F1-score | > 0.2 |
| Phase 6 | GVP-GNN trains without errors | Yes |
| Phase 8 | Test set F1-score | > 0.4 |
| Phase 8 | Top-10 precision | > 0.3 |
| Phase 8 | Test set AUPRC | > 0.25 |

---

## Timeline Estimate

- **Phase 1-2** (Setup & EDA): 1 week
- **Phase 3-4** (Preprocessing & Graphs): 2 weeks
- **Phase 5** (Baselines): 1 week
- **Phase 6-7** (GVP implementation & training): 2 weeks
- **Phase 8** (Evaluation): 1 week
- **Phase 9-10** (Inference & interpretability): 1 week
- **Phase 11** (Advanced improvements): 2-4 weeks (optional)
- **Phase 12** (Documentation): 1 week

**Total**: ~11-15 weeks for a complete implementation with evaluation.

---

## References & Resources

### Papers
- Dror Lab GVP Paper: "Learning from Protein Structure with Geometric Vector Perceptrons"
- ASBench: "ASBench: benchmarking sets for allosteric discovery"
- Allosite: "Computational methods for allosteric site identification"

### Code Repositories
- [drorlab/gvp-pytorch](https://github.com/drorlab/gvp-pytorch)
- PyTorch Geometric documentation
- Biopython PDB module

### Datasets
- ASBench Core Set
- RCSB PDB
- CATALYTIC SITE ATLAS (for active sites)

---

## Next Immediate Steps

1. **Set up environment** (`requirements.txt`, directories)
2. **Download ASBench dataset** and explore it
3. **Download a subset of PDB files** (start with 10-20 proteins)
4. **Build PDB parser** and validate on test proteins
5. **Implement negative sampling strategy** with stratification
6. **Build graph construction** and visualize sample graphs

Let's start building! 🚀

