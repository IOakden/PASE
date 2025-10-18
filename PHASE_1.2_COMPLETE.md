# ✅ Phase 1.2: Data Acquisition - COMPLETE

## What Was Accomplished

### 1. ASBench Dataset Acquisition
- [x] Downloaded ASBench Core Set from http://mdl.shsmu.edu.cn/ASBench/
- [x] Copied `AsBench_Core_Set.xls` to `data/asbench/`
- [x] Copied 235 PDB files to `data/pdb/`

### 2. ASBench Parsing
- [x] Created `scripts/parse_asbench.py` - Parse XLS and extract annotations
- [x] Generated `data/asbench/asbench_annotations.csv` - Structured annotations
- [x] Generated `data/asbench/asbench_annotations_raw.csv` - Raw CSV export
- [x] Generated `data/asbench/pdb_list.txt` - List of 230 unique PDB IDs

### 3. PDB Files
- [x] Copied 235 PDB files from ASBench `allosteric_proteins/` directory
- [x] Created `scripts/download_missing_pdbs.py` - Utility script for future use (not required for this project)
  - **Purpose**: Download clean PDB files from RCSB if needed
  - **Use case**: Get updated structures, work with custom protein lists, download without ASBench naming
  - **Note**: Not needed for current workflow since ASBench includes all files

### 4. Documentation
- [x] Created `data/asbench/DATASET_SUMMARY.md` - Comprehensive dataset overview

## Key Findings

### Dataset Statistics
- **Total entries**: 235 (allosteric sites)
- **Unique proteins**: 230 PDB IDs
- **PDB files**: 235 (some proteins have multiple sites)
- **Unique chains**: 12 (A-L)
- **File source**: Copied from ASBench distribution ✅

**Why 235 files for 230 proteins?** Some proteins have multiple allosteric sites with different modulators. Each site gets a separate entry and PDB file with ASBench naming: `AS{site_id}_{pdb_id}.pdb`

### Annotation Format
The ASBench annotations include:
- **PDB ID + Chain ID**: Identifies the protein structure and specific chain
- **Residue IDs**: Allosteric site residue positions (PDB numbering)
  - Single residue: `541`
  - Multiple residues: `800;900` (semicolon-separated)
  - Multiple chains: `A;D;E;H` with `1260;4260;5260;8260`
- **Modulator info**: Type (Activator/Inhibitor), chemical name, structure
- **Metadata**: Gene name, UniProt ID, organism, references

### Important Observations

1. **Multiple residues per site**: ~10% of entries have multiple allosteric residues
   - Example: 4BZB has residues 800 and 900
   - Example: 4FYY has residues 202, 203, 204

2. **Multi-chain sites**: Some allosteric sites span multiple chains
   - Example: 1XTU has chains A, D, E, H with different residue positions
   - Example: 3ETE has chains A, B, C, D, F

3. **Same protein, different sites**: Some PDB IDs appear multiple times
   - Indicates multiple allosteric sites or different modulators
   - Need to handle this in data splitting (group by PDB ID)

## Files Created

### Scripts
```
scripts/
├── parse_asbench.py          # Parse ASBench XLS to CSV
└── download_missing_pdbs.py   # Download PDB structures (if needed)
```

### Data Files
```
data/
├── asbench/
│   ├── AsBench_Core_Set.xls              # Original dataset
│   ├── asbench_annotations.csv           # Structured annotations
│   ├── asbench_annotations_raw.csv       # Raw CSV export
│   ├── pdb_list.txt                      # List of PDB IDs
│   └── DATASET_SUMMARY.md                # Dataset documentation
└── pdb/
    └── *.pdb                              # 235 PDB structure files
```

## Data Quality Considerations for Next Phase

### Phase 2 (Exploration) Will Need to Address:

1. **Residue numbering**: PDB numbering may have gaps (e.g., 1, 2, 5, 6...)
   - Need robust mapping between ASBench IDs and PDB residues
   - Handle insertion codes (e.g., 100A, 100B)

2. **Missing residues**: X-ray structures often have missing loops
   - Check if allosteric residues are present in structure
   - Flag proteins with >20% missing residues

3. **Multi-chain handling**: 
   - Parse biological assemblies correctly
   - Some allosteric sites at chain interfaces

4. **Class imbalance**: Estimated 0.5-1% positive class
   - Need stratified negative sampling
   - Exclude active sites from negatives
   - Exclude buffer zone (8-10Å) around allosteric sites

## Usage Examples

### Parse ASBench Annotations
```bash
# Already completed, but to re-run:
source venv/bin/activate
python scripts/parse_asbench.py
```

### Download Missing PDBs (if needed in future)
```bash
source venv/bin/activate
python scripts/download_missing_pdbs.py --pdb-list data/asbench/pdb_list.txt --output-dir data/pdb
```

### Access Annotations in Python
```python
import pandas as pd

# Load annotations
df = pd.read_csv('data/asbench/asbench_annotations.csv')

# Example: Get all allosteric sites for a specific protein
protein_3uo9 = df[df['pdb_id'] == '3UO9']
print(protein_3uo9[['pdb_id', 'chain_id', 'residue_ids']])

# Example: Count entries by modulator type
print(df['Modulator Type'].value_counts())
```

## Next Steps

### Phase 2: Data Exploration & Quality Assessment
Now that we have the data, the next phase involves:

1. **Create exploration notebook** (`notebooks/01_data_exploration.ipynb`):
   - Load and visualize annotations
   - Count allosteric residues per protein
   - Analyze class distribution
   - Check PDB structure quality (resolution, completeness)

2. **Data quality script** (`src/data_quality.py`):
   - Parse each PDB file
   - Map ASBench residues to PDB structure
   - Identify missing residues
   - Flag problematic structures

3. **Statistical analysis**:
   - Amino acid composition of allosteric sites
   - Secondary structure preferences
   - Surface accessibility distribution
   - Spatial clustering analysis

## Environment Notes

- **Virtual environment created**: `venv/`
- **Packages installed**: pandas, openpyxl, xlrd
- **Active shell**: Remember to activate venv with `source venv/bin/activate`

## Summary

✅ **Phase 1.2 COMPLETE**

- ASBench dataset acquired and parsed
- 230 unique proteins with 235 entries
- All PDB structures downloaded
- Annotations extracted and structured
- Ready for Phase 2: Data Exploration

**Time Taken**: ~15 minutes  
**Next Phase**: Phase 2.1 - Exploratory Data Analysis  
**Estimated Time**: 1-2 hours

