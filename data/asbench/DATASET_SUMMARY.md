# ASBench Core Set - Dataset Summary

## Overview

The ASBench Core Set contains experimentally validated allosteric proteins with detailed annotations about allosteric sites and modulators.

**Dataset Source**: http://mdl.shsmu.edu.cn/ASBench/

**Date Acquired**: October 18, 2025

## Statistics

- **Total Entries**: 235
- **Unique Proteins (PDB IDs)**: 230
- **Unique Chains**: 12
- **PDB Files**: 235

### Why 235 Files but Only 230 Unique PDB IDs?

Some proteins have **multiple allosteric sites** with different modulators or residue positions. Each site gets its own entry and PDB file.

**Example**: Pyruvate Kinase M (PKM) appears 3 times:
- Entry 1: `4B2D` with Serine activator at residue 1532
- Entry 2: `3H6O` with FBP activator at residue 541
- Entry 3: `4G1N` with NZT activator at residue 603

This is expected and correct - we want to train on all known allosteric sites.

## Data Structure

### Files Created

1. **`AsBench_Core_Set.xls`** - Original Excel file from ASBench
2. **`asbench_annotations_raw.csv`** - Raw CSV export of Excel file
3. **`asbench_annotations.csv`** - Structured annotations with cleaned columns
4. **`pdb_list.txt`** - List of 230 unique PDB IDs (for reference)
5. **`../../pdb/*.pdb`** - 235 PDB structure files

### PDB File Naming Convention

ASBench provides PDB files with prefixed naming:
```
AS{allosteric_site_id}_{pdb_id}.pdb
```

**Examples**:
- `AS001000501_3UO9.pdb` → Allosteric site AS001000501 in protein 3UO9
- `AS001001701_4B2D.pdb` → Allosteric site AS001001701 in protein 4B2D
- `AS001001702_3H6O.pdb` → Allosteric site AS001001702 in protein 3H6O

The prefix indicates which allosteric site annotation the file corresponds to. Multiple files may share the same PDB ID if the protein has multiple allosteric sites.

### Annotation Fields

The structured CSV contains the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `entry_id` | Sequential entry number | 0, 1, 2, ... |
| `pdb_id` | PDB structure identifier | 3UO9, 4B2D, 3H6O |
| `chain_id` | Chain identifier in PDB | A, B, C |
| `residue_ids` | Allosteric site residue numbers (PDB numbering) | 2, 1532, 541;603 |
| `protein_name` | Full protein name | "Glutaminase kidney isoform" |
| `allosteric_site` | ASBench site identifier | AS001000501 |
| `Gene Name` | Gene symbol | GLS, PKM, PKLR |
| `Uniprot ID` | UniProt accession | O94925, P14618 |
| `Organism` | Species | Homo sapiens |
| `Modulator Name` | Short modulator code | 04A, SER, FBP |
| `Modulator Full Name` | Chemical name of modulator | "2-phenyl-N-[5-..." |
| `Modulator Type` | Type of allosteric effect | Inhibitor, Activator, Modulator |
| `Reference` | Publication title | "Full-length human..." |
| `Pubmed ID` | PubMed identifier | 22049910 |

### Residue ID Format

Allosteric site residues are specified in the `residue_ids` column:
- **Single residue**: `541` (one residue at position 541)
- **Multiple residues**: `800;900` (residues at positions 800 and 900, semicolon-separated)
- **Note**: Residue numbering follows PDB convention (not sequential 1-N)

### Chain Information

Most proteins have single chains, but some are multi-chain complexes:
- Unique chain IDs: A, B, C, D, E, F, G, H, I, J, K, L
- Most common: Chain A

## Data Quality Notes

### Strengths
- ✅ All PDB structures available and downloaded
- ✅ Experimentally validated allosteric sites
- ✅ Rich metadata (organism, gene, modulator, references)
- ✅ Includes both activators and inhibitors

### Considerations
- ⚠️ Some entries have the same PDB ID but different chains or allosteric sites
- ⚠️ Residue numbering may have gaps due to PDB conventions
- ⚠️ Some PDB files may have missing residues (common in X-ray structures)
- ⚠️ Need to handle residue numbering mismatches between ASBench and PDB

## Expected Class Imbalance

Based on 230-235 proteins:
- **Total residues**: ~100,000 (assuming ~300 residues per protein)
- **Allosteric residues**: ~500-1,000 (estimated 2-5 residues per site)
- **Class imbalance**: ~0.5-1% positive class

This severe imbalance requires:
1. Careful negative sampling strategy
2. Appropriate evaluation metrics (AUPRC, not just accuracy)
3. Weighted loss functions or focal loss

## Next Steps

### Phase 2: Data Exploration
- [ ] Count exact number of allosteric residues per protein
- [ ] Analyze residue types (amino acid distribution)
- [ ] Check PDB structure quality (resolution, missing residues)
- [ ] Visualize spatial distribution of allosteric sites

### Phase 3: Preprocessing
- [ ] Parse PDB files and extract atom coordinates
- [ ] Map ASBench residue IDs to PDB residues
- [ ] Handle residue numbering mismatches
- [ ] Generate negative labels with stratified sampling
- [ ] Compute structural features (SASA, depth, secondary structure)

## Sample Entries

### Entry 0: Glutaminase (3UO9)
- **PDB ID**: 3UO9, Chain B
- **Allosteric Site**: Position 2
- **Modulator**: 04A (Inhibitor)
- **Organism**: Human

### Entry 1: Pyruvate Kinase (4B2D)
- **PDB ID**: 4B2D, Chain A
- **Allosteric Site**: Position 1532
- **Modulator**: Serine (Activator)
- **Organism**: Human

### Entry 14: SAMHD1 (4BZB)
- **PDB ID**: 4BZB, Chain A
- **Allosteric Sites**: Positions 800 and 900 (multiple sites)
- **Modulator**: DGT (Activator)
- **Organism**: Human

## References

- ASBench Database: http://mdl.shsmu.edu.cn/ASBench/
- RCSB PDB: https://www.rcsb.org/
- Original ASBench Paper: "ASBench: benchmarking sets for allosteric discovery"

