# Engineering Roadmap: Allosteric Site Prediction

## Phase 1: Setup & Data Acquisition

### 1.1 Environment Setup
- [x] Create virtual environment (Python 3.8+)
- [x] Install dependencies: PyTorch ≥2.0, PyTorch Geometric, Biopython, pandas, numpy, scikit-learn
- [x] Create directory structure: data/pdb, data/asbench, src/, outputs/, notebooks/
- [x] Configure git with .gitignore
- [x] Create config.yaml for hyperparameters and paths

### 1.2 Data Acquisition
- [x] Download ASBench Core Set (http://mdl.shsmu.edu.cn/ASBench/) → `data/asbench/ASBench_Core_Set.xls`
- [x] Parse ASBench XLS: extract PDB ID, Chain ID, Residue IDs, annotations
- [x] Download 230 PDB structures (already included with ASBench)

---

## Phase 2: Data Validation

**Goal**: Validate that modulators exist in PDB structures and compute allosteric sites as residues within 5Å of bound modulators.

**Key Insight**: ASBench "Residue ID (PDB)" refers to the MODULATOR (ligand), not protein residues. Allosteric sites are defined as protein residues in contact with (< 5Å from) the modulator.

**Philosophy**: Skip exploratory analysis and visualization. Focus only on blocking issues that would prevent model training. Exploration can be done later if needed.

### 2.1 Dataset Validation Script (`src/validate_dataset.py`)

**Implement**:
- [x] `validate_protein(pdb_file, asbench_row)`:
  - Parse PDB structure with Biopython
  - Extract all residues from structure
  - Map ASBench residue IDs to PDB residues (handle numbering gaps, insertion codes)
  - Count: total_residues, allosteric_residues, missing_residues, matched_annotations
  - Check resolution from PDB header
  - Return: `ValidationResult(pdb_id, status, metrics)`

- [x] `validate_all_proteins(annotations_csv, pdb_dir)`:
  - Load annotations from `data/asbench/asbench_annotations.csv`
  - Process all 235 entries (230 unique proteins)
  - Track validation status: 'ok', 'warning', 'failed'
  - Generate `data/processed/validation_report.csv`:
    ```csv
    pdb_file,pdb_id,chain_id,total_residues,allosteric_residues,missing_residues,
    annotation_matched,resolution,status,notes
    ```
  - Print summary statistics:
    - Class imbalance: "X allosteric residues / Y total residues (Z%)"
    - Proteins by status: "N ok, M warning, K failed"
  - Save usable proteins: `data/processed/clean_proteins.txt`
    - Criteria: annotation_matched=True, missing_residues<20%, status='ok'

- [x] Run validation:
  ```bash
  python src/validate_dataset.py
  ```
  - Actual output:
    ```
    Validating 235 entries...
    ✓ 60 proteins validated successfully
    ⚠ 56 proteins with warnings (minor issues)
    ✗ 119 proteins failed (modulator not found)
    
    Class imbalance: 2,137 allosteric / 47,946 total residues (4.46%)
    Saved clean protein list: data/processed/clean_proteins.txt (60 proteins)
    Saved usable protein list: data/processed/usable_proteins.txt (116 proteins)
    Saved validation report: data/processed/validation_report.csv
    ```

---

## Phase 3: Preprocessing

### 3.1 PDB Parser (`src/preprocessing.py`)

**Implement**:
- [x] `parse_pdb(pdb_file)` → dict with:
  - `coords`: numpy array (N_atoms, 3)
  - `residues`: list of (chain_id, res_num, res_name)
  - `atoms`: list of (atom_name, element)
  - `b_factors`: numpy array

- [x] `compute_residue_features(structure)` → DataFrame with columns:
  - `chain_id`, `res_num`, `res_name`
  - `sasa` (use FreeSASA or Biopython)
  - `depth` (distance from surface)
  - `secondary_structure` (use DSSP: H=helix, E=sheet, C=coil)
  - `ca_coords` (x, y, z)

### 3.2 Label Generator (`src/labeling.py`)

**Implement**:
- [x] `generate_positive_labels(asbench_annotations, pdb_structure)`:
  - Find modulator (HETATM) using ASBench modulator residue ID
  - Compute protein residues within 5Å of modulator using spatial distance
  - Use Biopython NeighborSearch for efficient distance calculation
  - Return list of (chain_id, res_num) tuples for allosteric site
  - Label = 1

- [x] `generate_negative_labels(pdb_structure, positive_labels, active_sites=None)`:
  - Exclude residues within 10Å of any allosteric residue
  - Exclude active site residues (if available)
  - Stratified sampling:
    - 40% surface-exposed (SASA > 20 Å²)
    - 40% buried (SASA < 20 Å²)
    - 20% intermediate
  - Balance: 1:3 positive:negative ratio
  - Label = 0

- [x] `create_label_dataset(proteins_list)` → save to `data/processed/labels.csv`
  - Columns: pdb_id, chain_id, res_num, label
  
**Results**:
- Processed: 217 proteins successfully
- Generated: 18,217 total labels (4,579 positive, 13,638 negative)
- Ratio: 1:2.98 (target was 1:3)
- Features computed: SASA, depth, secondary structure, Cα coordinates

---

## Phase 4: Graph Construction

### 4.1 Graph Builder (`src/graph_builder.py`)

**Implement**:
- [ ] `build_protein_graph(pdb_file, features_df, labels_df)`:
  
  **Nodes** (residue-level):
  - Position: Cα coordinates (x, y, z)
  - Scalar features (dim=25):
    - Residue type one-hot (20)
    - SASA (1)
    - Depth (1)
    - B-factor (1)
    - Secondary structure one-hot (3: H/E/C)
  - Vector features (dim=2 vectors):
    - Backbone orientation: N→Cα, Cα→C
  - Labels: binary (0/1)
  
  **Edges** (KNN with K=10):
  - Edge index: connect each node to 10 nearest neighbors
  - Scalar features: Euclidean distance
  - Vector features: unit direction vector
  
  Return: `torch_geometric.data.Data` object

- [ ] `build_dataset(protein_list)`:
  - Process all 320 proteins
  - Save graphs to `data/processed/graphs/`
  - Use PyTorch Geometric InMemoryDataset format

### 4.2 Data Validation
- [ ] Script: `validate_graphs.py`
  - Check for isolated nodes
  - Plot node degree distribution
  - Verify feature dimensions: scalar (25), vector (2, 3)
  - Test DataLoader batching

---

## Phase 5: Baselines

### 5.1 Baseline Models (`src/baselines.py`)

**Implement**:
- [ ] `RandomBaseline`: random predictions → measure expected precision (~2%)
- [ ] `LogisticRegression`: features = [residue_type, SASA, depth, b_factor]
- [ ] `RandomForest`: same features, tune n_estimators and max_depth
- [ ] `SimpleGCN`: 3-layer GCN with only scalar features (no vectors)

**Script** (`scripts/train_baselines.py`):
- [ ] Train/val/test split: 224/48/48 proteins (70/15/15%)
- [ ] Evaluate: Precision, Recall, F1, AUROC, AUPRC
- [ ] Save results to `outputs/baseline_results.csv`

---

## Phase 6: GVP-GNN Model

### 6.1 Model Implementation (`src/gvp_model.py`)

**Use**: `drorlab/gvp-pytorch` library

**Implement**:
- [ ] `class AlloGVP(nn.Module)`:
  
  **Architecture**:
  - Input embedding: project (25, 2) → (128, 16)
  - 4x GVP-GNN layers with message passing
  - Residual connections after each layer
  - Layer normalization
  - Output head:
    - Pool vectors: take norms → scalars
    - MLP: 128 → 256 → 128 → 1
    - Sigmoid for binary classification
  
  **Forward**:
  ```python
  def forward(self, node_s, node_v, edge_index, edge_s, edge_v, batch):
      # node_s: (N, 128) scalars
      # node_v: (N, 16, 3) vectors
      # Returns: (N, 1) probabilities
  ```

- [ ] `class FocalLoss(nn.Module)`: implement focal loss with alpha=0.25, gamma=2.0

### 6.2 Hyperparameters (`config.yaml`)
```yaml
model:
  hidden_dims: [128, 16]
  num_layers: 4
  dropout: 0.2
  mlp_dims: [256, 128]

training:
  lr: 0.0005
  weight_decay: 0.0001
  batch_size: 8
  epochs: 100
  loss: focal_loss
```

---

## Phase 7: Training

### 7.1 Data Splitting (`src/data_split.py`)
- [ ] `split_proteins(protein_list, seed=42)`:
  - Use CD-HIT or MMseqs2 for sequence clustering at 30% identity
  - Ensure no homologs across train/val/test
  - Stratify by protein size
  - Save splits to `data/processed/splits/{train,val,test}.txt`

### 7.2 Training Script (`src/train.py`)

**Implement**:
- [ ] `class Trainer`:
  - Mixed precision training (torch.cuda.amp)
  - Gradient accumulation (if memory limited)
  - Learning rate scheduler: ReduceLROnPlateau (patience=10)
  - Early stopping: patience=20 on val_f1
  - Checkpoint saving: best model by val_f1
  
- [ ] Training loop:
  ```python
  for epoch in range(num_epochs):
      train_loss = train_epoch(model, train_loader, optimizer)
      val_metrics = evaluate(model, val_loader)
      log_metrics(epoch, train_loss, val_metrics)
      scheduler.step(val_metrics['f1'])
      if early_stop.should_stop(val_metrics['f1']):
          break
  ```

- [ ] Logging: TensorBoard
  - Track: loss, precision, recall, f1, auroc, auprc
  - Plot per-epoch curves

### 7.3 Run Command
```bash
python src/train.py --config config.yaml --output outputs/models/gvp_v1.pt
```

---

## Phase 8: Evaluation

### 8.1 Evaluation Script (`src/evaluate.py`)

**Implement**:
- [ ] `evaluate_model(model, test_loader)`:
  - Compute: Precision, Recall, F1, AUROC, AUPRC
  - Top-K accuracy: K=5, 10, 20 (per protein)
  - Confusion matrix
  - Per-protein F1 scores
  - Save to `outputs/test_results.json`

- [ ] `plot_results(predictions, labels)`:
  - ROC curve
  - PR curve
  - Per-protein F1 distribution
  - Save figures to `outputs/figures/`

### 8.2 Ablation Studies (`scripts/ablation.py`)
- [ ] Remove vector features → measure ΔF1
- [ ] Shuffle node positions → measure ΔF1
- [ ] Vary KNN: K=5, 10, 15, 20 → plot F1 vs K
- [ ] Vary GVP layers: 2, 3, 4, 5 → plot F1 vs layers

### 8.3 Error Analysis (`notebooks/02_error_analysis.ipynb`)
- [ ] Load false positives: check if near allosteric sites (within 5-10Å)
- [ ] Load false negatives: check SASA, depth, secondary structure distributions
- [ ] Visualize error cases in PyMOL

---

## Phase 9: Inference

### 9.1 Inference Pipeline (`src/inference.py`)

**Implement**:
- [ ] `predict_allosteric_sites(pdb_file, model_path)`:
  ```python
  # 1. Parse PDB
  structure = parse_pdb(pdb_file)
  # 2. Compute features
  features = compute_residue_features(structure)
  # 3. Build graph
  graph = build_protein_graph(pdb_file, features, labels=None)
  # 4. Run inference
  model.eval()
  probs = model(graph)
  # 5. Return DataFrame: chain_id, res_num, probability
  return results_df
  ```

- [ ] Handle edge cases:
  - Missing residues: skip, log warning
  - Non-standard amino acids: map to closest standard (e.g., MSE→MET)
  - Multi-chain: process each chain separately

### 9.2 Visualization (`src/visualization.py`)

**Implement**:
- [ ] `generate_pymol_script(pdb_file, predictions, output_pml)`:
  - Color residues by probability: blue (0.0) → red (1.0)
  - Highlight top-10 predictions as sticks
  - Save script to run in PyMOL

- [ ] `visualize_in_nglview(pdb_file, predictions)`:
  - Return NGLview widget for Jupyter
  - Color by probability gradient

- [ ] `plot_predictions(predictions_df)`:
  - Histogram of probabilities
  - Top-20 predictions table
  - Save figure

### 9.3 CLI Tool (`scripts/predict.py`)
```bash
python scripts/predict.py --pdb data/pdb/1ABC.pdb --model outputs/models/gvp_v1.pt --output outputs/predictions/1ABC_predictions.csv --visualize
```

---

## Phase 10: Advanced (Optional)

### 10.1 Semi-Supervised Pre-training
- [ ] Download unlabeled PDB structures (10K proteins)
- [ ] Self-supervised task: mask residues, predict residue type
- [ ] Pre-train GVP encoder
- [ ] Fine-tune on ASBench

### 10.2 Multi-Task Learning
- [ ] Add active site prediction head (if active site data available)
- [ ] Shared GVP encoder, two output heads
- [ ] Joint loss: L = L_allosteric + 0.5 * L_active

### 10.3 Model Interpretability
- [ ] Implement GNNExplainer for GVP
- [ ] Extract important subgraphs for each prediction
- [ ] Visualize attention weights (if using attention)

---

## Deliverables Summary

### Code Files
- `src/validate_dataset.py`: validate PDB structures and annotations
- `src/preprocessing.py`: PDB parsing, feature computation
- `src/labeling.py`: positive/negative label generation
- `src/graph_builder.py`: graph construction for PyG
- `src/baselines.py`: baseline models
- `src/gvp_model.py`: GVP-GNN implementation
- `src/train.py`: training loop
- `src/evaluate.py`: evaluation metrics
- `src/inference.py`: prediction pipeline
- `src/visualization.py`: PyMOL/NGLview visualization

### Scripts
- `scripts/parse_asbench.py`: parse ASBench XLS to CSV
- `scripts/download_missing_pdbs.py`: download PDB files (optional utility)
- `scripts/train_baselines.py`: train baseline models
- `scripts/ablation.py`: ablation studies
- `scripts/predict.py`: CLI for inference

### Notebooks (Optional)
- `notebooks/error_analysis.ipynb`: analyze predictions after training
- `notebooks/exploration.ipynb`: exploratory analysis if needed

### Outputs
- `data/processed/validation_report.csv`: data quality validation results
- `data/processed/clean_proteins.txt`: list of usable proteins
- `outputs/models/gvp_v1.pt`: trained model checkpoint
- `outputs/baseline_results.csv`: baseline performance
- `outputs/test_results.json`: final test metrics
- `outputs/figures/`: plots and visualizations

---

## Target Metrics

| Metric | Target |
|--------|--------|
| Test F1 | > 0.4 |
| Test AUPRC | > 0.25 |
| Top-10 Precision | > 0.3 |
| Baseline improvement | +0.2 F1 |
