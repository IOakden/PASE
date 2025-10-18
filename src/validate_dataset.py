#!/usr/bin/env python3
"""
Dataset validation script for ASBench + PDB structures.

Validates that ASBench annotations map correctly to PDB structures and 
identifies usable proteins for model training.
"""

import os
import sys
import re
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
from Bio.PDB import PDBParser, PDBIO
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import warnings

# Suppress Biopython PDB warnings (common and usually non-critical)
warnings.filterwarnings('ignore', category=PDBConstructionWarning)


@dataclass
class ValidationResult:
    """Results from validating a single protein."""
    pdb_file: str
    pdb_id: str
    chain_id: str
    total_residues: int
    allosteric_residues: int
    missing_residues: int
    annotation_matched: bool
    resolution: Optional[float]
    status: str  # 'ok', 'warning', 'failed'
    notes: str


def parse_pdb_structure(pdb_file):
    """
    Parse PDB file and extract structure.
    
    Args:
        pdb_file: Path to PDB file
        
    Returns:
        structure: Biopython Structure object, or None if parsing fails
    """
    parser = PDBParser(QUIET=True)
    try:
        structure = parser.get_structure('protein', pdb_file)
        return structure
    except Exception as e:
        print(f"    Error parsing PDB: {e}")
        return None


def get_resolution(structure):
    """
    Extract resolution from PDB header.
    
    Args:
        structure: Biopython Structure object
        
    Returns:
        resolution: float in Angstroms, or None if not available
    """
    try:
        resolution = structure.header.get('resolution')
        return resolution
    except:
        return None


def get_residues_from_chain(structure, chain_id):
    """
    Get all residues from a specific chain.
    
    Args:
        structure: Biopython Structure object
        chain_id: Chain identifier (e.g., 'A', 'B')
        
    Returns:
        residues: dict mapping residue_id to residue object
    """
    residues = {}
    
    for model in structure:
        if chain_id not in [c.id for c in model]:
            continue
            
        chain = model[chain_id]
        for residue in chain:
            # Skip heteroatoms (water, ligands, etc.)
            if residue.id[0] == ' ':  # Standard amino acid
                res_num = residue.id[1]
                insertion_code = residue.id[2].strip()
                
                # Create residue identifier (handle insertion codes)
                if insertion_code:
                    res_id = f"{res_num}{insertion_code}"
                else:
                    res_id = str(res_num)
                
                residues[res_id] = residue
    
    return residues


def parse_allosteric_residues(residue_ids_str):
    """
    Parse allosteric residue IDs from ASBench annotation.
    
    Handles formats like:
    - "541" (single residue)
    - "800;900" (multiple residues, semicolon-separated)
    - "202;203;204" (multiple consecutive residues)
    
    Args:
        residue_ids_str: String of residue IDs from ASBench
        
    Returns:
        residue_ids: List of residue ID strings
    """
    if pd.isna(residue_ids_str):
        return []
    
    residue_ids_str = str(residue_ids_str).strip()
    
    # Split by semicolon
    if ';' in residue_ids_str:
        residue_ids = [rid.strip() for rid in residue_ids_str.split(';')]
    else:
        residue_ids = [residue_ids_str]
    
    return residue_ids


def parse_chain_ids(chain_ids_str):
    """
    Parse chain IDs from ASBench annotation.
    
    Handles formats like:
    - "A" (single chain)
    - "A;D;E;H" (multiple chains, semicolon-separated)
    
    Args:
        chain_ids_str: String of chain IDs from ASBench
        
    Returns:
        chain_ids: List of chain ID strings
    """
    if pd.isna(chain_ids_str):
        return ['A']  # Default to chain A
    
    chain_ids_str = str(chain_ids_str).strip()
    
    # Split by semicolon
    if ';' in chain_ids_str:
        chain_ids = [cid.strip() for cid in chain_ids_str.split(';')]
    else:
        chain_ids = [chain_ids_str]
    
    return chain_ids


def get_allosteric_residues_near_modulator(structure, chain_id, modulator_res_id, distance_cutoff=5.0):
    """
    Find protein residues near a modulator (HETATM).
    
    The allosteric site is defined as protein residues within distance_cutoff Angstroms
    of the modulator molecule.
    
    Args:
        structure: Biopython Structure object
        chain_id: Chain ID containing the modulator
        modulator_res_id: Residue ID of the modulator (HETATM)
        distance_cutoff: Distance threshold in Angstroms
        
    Returns:
        allosteric_residues: List of (chain_id, res_num) tuples
    """
    from Bio.PDB import NeighborSearch
    
    allosteric_residues = []
    
    for model in structure:
        if chain_id not in [c.id for c in model]:
            continue
        
        chain = model[chain_id]
        
        # Find modulator residue (HETATM)
        modulator_residue = None
        for residue in chain:
            # HETATM residues have non-blank hetero flag
            if residue.id[0] != ' ':  # Not a standard amino acid
                res_id_num = residue.id[1]
                if str(res_id_num) == str(modulator_res_id):
                    modulator_residue = residue
                    break
        
        if not modulator_residue:
            return []
        
        # Get all atoms in the structure
        atom_list = []
        residue_map = {}
        
        for res in chain:
            if res.id[0] == ' ':  # Standard amino acid only
                for atom in res:
                    atom_list.append(atom)
                    residue_map[atom] = res
        
        # Build neighbor search
        ns = NeighborSearch(atom_list)
        
        # Find atoms near modulator
        nearby_residues = set()
        for mod_atom in modulator_residue:
            nearby_atoms = ns.search(mod_atom.coord, distance_cutoff)
            for atom in nearby_atoms:
                if atom in residue_map:
                    res = residue_map[atom]
                    res_num = res.id[1]
                    insertion_code = res.id[2].strip()
                    if insertion_code:
                        res_id_str = f"{res_num}{insertion_code}"
                    else:
                        res_id_str = str(res_num)
                    nearby_residues.add((chain_id, res_id_str))
        
        allosteric_residues = list(nearby_residues)
    
    return allosteric_residues


def validate_protein(pdb_file, asbench_row):
    """
    Validate a single protein structure against ASBench annotations.
    
    Allosteric sites are defined as protein residues within 5Å of the modulator molecule.
    
    Args:
        pdb_file: Path to PDB file
        asbench_row: Row from ASBench annotations DataFrame
        
    Returns:
        ValidationResult object
    """
    pdb_id = asbench_row['pdb_id']
    chain_id_str = asbench_row['chain_id']
    modulator_res_ids_str = asbench_row['residue_ids']  # This is modulator residue ID, not allosteric site!
    
    # Parse structure
    structure = parse_pdb_structure(pdb_file)
    if structure is None:
        return ValidationResult(
            pdb_file=os.path.basename(pdb_file),
            pdb_id=pdb_id,
            chain_id=chain_id_str,
            total_residues=0,
            allosteric_residues=0,
            missing_residues=0,
            annotation_matched=False,
            resolution=None,
            status='failed',
            notes='Failed to parse PDB file'
        )
    
    # Get resolution
    resolution = get_resolution(structure)
    
    # Parse chain IDs and modulator residue IDs
    chain_ids = parse_chain_ids(chain_id_str)
    modulator_res_ids = parse_allosteric_residues(modulator_res_ids_str)
    
    # Validate each chain and find allosteric residues
    total_residues = 0
    all_allosteric_residues = []
    missing_count = 0
    notes = []
    modulator_found = False
    
    for chain_id in chain_ids:
        # Get residues from chain
        residues = get_residues_from_chain(structure, chain_id)
        
        if not residues:
            notes.append(f"Chain {chain_id} not found or empty")
            continue
        
        total_residues += len(residues)
        
        # Find allosteric residues near modulator
        for mod_res_id in modulator_res_ids:
            allo_residues = get_allosteric_residues_near_modulator(structure, chain_id, mod_res_id, distance_cutoff=5.0)
            if allo_residues:
                all_allosteric_residues.extend(allo_residues)
                modulator_found = True
            else:
                notes.append(f"Modulator {mod_res_id} not found or no nearby protein residues in chain {chain_id}")
    
    # Remove duplicates from allosteric residues
    all_allosteric_residues = list(set(all_allosteric_residues))
    num_allosteric = len(all_allosteric_residues)
    
    # Check for missing residues (gaps in numbering)
    for chain_id in chain_ids:
        residues = get_residues_from_chain(structure, chain_id)
        if residues:
            res_nums = []
            for res_id in residues.keys():
                try:
                    # Extract numeric part
                    num = int(re.match(r'(\d+)', res_id).group(1))
                    res_nums.append(num)
                except:
                    pass
            
            if res_nums:
                res_nums.sort()
                expected_count = res_nums[-1] - res_nums[0] + 1
                actual_count = len(res_nums)
                missing_count += (expected_count - actual_count)
    
    # Determine status
    missing_percent = (missing_count / total_residues * 100) if total_residues > 0 else 0
    
    if not modulator_found or num_allosteric == 0:
        status = 'failed'
        if not modulator_found:
            notes.append(f"Modulator not found in structure")
        if num_allosteric == 0:
            notes.append(f"No allosteric residues found near modulator")
    elif missing_percent > 20:
        status = 'failed'
        notes.append(f"Too many missing residues: {missing_percent:.1f}%")
    elif missing_percent > 5 or missing_count > 0:
        status = 'warning'
        if missing_count > 0:
            notes.append(f"{missing_count} missing residues ({missing_percent:.1f}%)")
        notes.append(f"Found {num_allosteric} allosteric residues")
    else:
        status = 'ok'
        notes.append(f"Found {num_allosteric} allosteric residues within 5Å of modulator")
    
    notes_str = '; '.join(notes) if notes else 'OK'
    
    return ValidationResult(
        pdb_file=os.path.basename(pdb_file),
        pdb_id=pdb_id,
        chain_id=chain_id_str,
        total_residues=total_residues,
        allosteric_residues=num_allosteric,
        missing_residues=missing_count,
        annotation_matched=modulator_found and num_allosteric > 0,
        resolution=resolution,
        status=status,
        notes=notes_str
    )


def validate_all_proteins(annotations_csv, pdb_dir, output_dir):
    """
    Validate all proteins in the dataset.
    
    Args:
        annotations_csv: Path to ASBench annotations CSV
        pdb_dir: Directory containing PDB files
        output_dir: Directory for output files
        
    Returns:
        results_df: DataFrame with validation results
    """
    print("=" * 60)
    print("Dataset Validation")
    print("=" * 60)
    
    # Load annotations
    print(f"\nLoading annotations from {annotations_csv}...")
    df = pd.read_csv(annotations_csv)
    print(f"Found {len(df)} entries ({df['pdb_id'].nunique()} unique proteins)")
    
    # Validate each entry
    results = []
    
    print(f"\nValidating {len(df)} entries...")
    for idx, row in df.iterrows():
        pdb_id = row['pdb_id']
        allosteric_site = row.get('allosteric_site', '')
        
        # Find PDB file (handle ASBench naming: AS{site_id}_{pdb_id}.pdb)
        pdb_pattern = f"*{pdb_id}*.pdb"
        pdb_files = list(Path(pdb_dir).glob(pdb_pattern))
        
        if not pdb_files:
            print(f"  [{idx+1}/{len(df)}] {pdb_id}: PDB file not found")
            results.append(ValidationResult(
                pdb_file='',
                pdb_id=pdb_id,
                chain_id=row['chain_id'],
                total_residues=0,
                allosteric_residues=0,
                missing_residues=0,
                annotation_matched=False,
                resolution=None,
                status='failed',
                notes='PDB file not found'
            ))
            continue
        
        # Use first matching file (or file with matching allosteric site ID)
        pdb_file = pdb_files[0]
        for pf in pdb_files:
            if allosteric_site and allosteric_site in pf.name:
                pdb_file = pf
                break
        
        # Validate
        result = validate_protein(str(pdb_file), row)
        results.append(result)
        
        # Print progress
        status_symbol = {
            'ok': '✓',
            'warning': '⚠',
            'failed': '✗'
        }.get(result.status, '?')
        
        print(f"  [{idx+1}/{len(df)}] {pdb_id} ({result.chain_id}): {status_symbol} {result.status.upper()}")
        if result.status != 'ok':
            print(f"      → {result.notes}")
    
    # Convert to DataFrame
    results_df = pd.DataFrame([
        {
            'pdb_file': r.pdb_file,
            'pdb_id': r.pdb_id,
            'chain_id': r.chain_id,
            'total_residues': r.total_residues,
            'allosteric_residues': r.allosteric_residues,
            'missing_residues': r.missing_residues,
            'annotation_matched': r.annotation_matched,
            'resolution': r.resolution,
            'status': r.status,
            'notes': r.notes
        }
        for r in results
    ])
    
    # Save validation report
    report_path = Path(output_dir) / 'validation_report.csv'
    results_df.to_csv(report_path, index=False)
    print(f"\n✓ Saved validation report: {report_path}")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    status_counts = results_df['status'].value_counts()
    print(f"\n✓ {status_counts.get('ok', 0)} proteins validated successfully")
    print(f"⚠ {status_counts.get('warning', 0)} proteins with warnings (minor issues)")
    print(f"✗ {status_counts.get('failed', 0)} proteins failed validation")
    
    # Class imbalance
    usable = results_df[results_df['status'].isin(['ok', 'warning'])]
    total_res = usable['total_residues'].sum()
    total_allo = usable['allosteric_residues'].sum()
    
    if total_res > 0:
        imbalance_pct = (total_allo / total_res) * 100
        print(f"\nClass imbalance: {total_allo:,} allosteric / {total_res:,} total residues ({imbalance_pct:.2f}%)")
    
    # Resolution statistics
    with_resolution = results_df[results_df['resolution'].notna()]
    if len(with_resolution) > 0:
        print(f"\nResolution statistics:")
        print(f"  Mean: {with_resolution['resolution'].mean():.2f} Å")
        print(f"  Median: {with_resolution['resolution'].median():.2f} Å")
        print(f"  Range: {with_resolution['resolution'].min():.2f} - {with_resolution['resolution'].max():.2f} Å")
    
    # Save clean proteins list
    clean_proteins = results_df[
        (results_df['status'] == 'ok') & 
        (results_df['annotation_matched'] == True)
    ]
    
    clean_list_path = Path(output_dir) / 'clean_proteins.txt'
    with open(clean_list_path, 'w') as f:
        for _, row in clean_proteins.iterrows():
            f.write(f"{row['pdb_file']}\n")
    
    print(f"\n✓ Saved {len(clean_proteins)} clean proteins: {clean_list_path}")
    
    # Save usable proteins (ok + warning)
    usable_proteins = results_df[
        (results_df['status'].isin(['ok', 'warning'])) & 
        (results_df['annotation_matched'] == True)
    ]
    
    usable_list_path = Path(output_dir) / 'usable_proteins.txt'
    with open(usable_list_path, 'w') as f:
        for _, row in usable_proteins.iterrows():
            f.write(f"{row['pdb_file']}\n")
    
    print(f"✓ Saved {len(usable_proteins)} usable proteins (ok + warning): {usable_list_path}")
    
    return results_df


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    annotations_csv = project_root / "data" / "asbench" / "asbench_annotations.csv"
    pdb_dir = project_root / "data" / "pdb"
    output_dir = project_root / "data" / "processed"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if files exist
    if not annotations_csv.exists():
        print(f"Error: Annotations file not found: {annotations_csv}")
        print("Please run: python scripts/parse_asbench.py")
        return 1
    
    if not pdb_dir.exists():
        print(f"Error: PDB directory not found: {pdb_dir}")
        return 1
    
    # Run validation
    results_df = validate_all_proteins(annotations_csv, pdb_dir, output_dir)
    
    print("\n" + "=" * 60)
    print("✓ Validation complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

