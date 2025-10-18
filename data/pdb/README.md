# PDB Structure Files

This directory contains protein structure files for all proteins in the ASBench Core Set.

## File Naming Convention

Files follow ASBench's naming convention:
```
AS{allosteric_site_id}_{pdb_id}.pdb
```

**Examples**:
- `AS001000501_3UO9.pdb` → Site AS001000501 in protein 3UO9
- `AS001001701_4B2D.pdb` → Site AS001001701 in protein 4B2D
- `AS001001702_3H6O.pdb` → Site AS001001702 in protein 3H6O

## File Statistics

- **Total files**: 235
- **Unique PDB IDs**: 230
- **File source**: ASBench Core Set distribution
- **Average file size**: ~300 KB per structure

## Why Multiple Files Per Protein?

Some proteins have **multiple allosteric sites** with different:
- Modulators (activators vs inhibitors)
- Binding residues
- Biological contexts

Each allosteric site gets its own entry and file. This is intentional and correct.

**Example - Pyruvate Kinase (PKM)**:
- `AS001001701_4B2D.pdb` - Serine activator site
- `AS001001702_3H6O.pdb` - FBP (Fructose-1,6-bisphosphate) activator site
- `AS001001703_4G1N.pdb` - NZT small molecule activator site

All three are the same protein (PKM) but represent different allosteric mechanisms.

## File Format

Standard PDB format with:
- **ATOM records**: Atomic coordinates (x, y, z)
- **HETATM records**: Heteroatoms (ligands, waters, ions)
- **HEADER**: PDB ID, classification, deposition date
- **SEQRES**: Primary sequence
- **CONECT**: Bond connectivity

## Working with These Files

### Parse with Biopython
```python
from Bio.PDB import PDBParser

parser = PDBParser()
structure = parser.get_structure('protein', 'AS001000501_3UO9.pdb')

# Access chains and residues
for model in structure:
    for chain in model:
        for residue in chain:
            print(f"Chain {chain.id}, Residue {residue.id}")
```

### Extract PDB ID from Filename
```python
import re

filename = "AS001000501_3UO9.pdb"
pdb_id = re.search(r'_([A-Z0-9]{4})\.pdb', filename).group(1)
# pdb_id = "3UO9"
```

### Get Allosteric Site ID
```python
filename = "AS001000501_3UO9.pdb"
site_id = filename.split('_')[0]
# site_id = "AS001000501"
```

## Downloading Clean PDB Files (Optional)

If you need PDB files without the ASBench prefix:

```bash
# Download from RCSB using utility script
python scripts/download_missing_pdbs.py --pdb-list data/asbench/pdb_list.txt --output-dir data/pdb_clean/
```

This downloads files as: `3UO9.pdb`, `4B2D.pdb`, etc.

## File Quality

### Resolution
Most structures are high-quality X-ray crystallography:
- Typical resolution: 1.5-3.0 Å
- Better resolution = more accurate atomic positions

### Common Issues
- **Missing residues**: Flexible loops often not resolved in crystals
- **Multiple models**: NMR structures may have multiple conformations
- **Insertion codes**: Residue numbering may have gaps or insertions (e.g., 100A, 100B)

These are handled in the preprocessing pipeline (Phase 3).

## Storage

- **Current size**: ~70 MB for 235 files
- **.gitignore**: Files are ignored by git (too large for version control)
- **Backup**: Keep original ASBench distribution as backup

## Next Steps

These files will be:
1. **Parsed** to extract atom coordinates and residue information
2. **Validated** to check quality and match with annotations
3. **Processed** to compute structural features (SASA, depth, secondary structure)
4. **Converted** to graph representations for GVP-GNN

See `ROADMAP.md` for details.

