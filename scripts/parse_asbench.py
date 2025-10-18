#!/usr/bin/env python3
"""
Parse ASBench Core Set XLS file and extract annotations.
Creates a structured CSV with PDB ID, Chain ID, Residue IDs, and allosteric site info.
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_asbench_xls(xls_path, output_csv):
    """
    Parse ASBench XLS file and extract allosteric site annotations.
    
    Args:
        xls_path: Path to AsBench_Core_Set.xls
        output_csv: Output path for parsed CSV
    """
    print(f"Reading {xls_path}...")
    
    # Read the XLS file
    # ASBench typically has the data in the first sheet
    df = pd.read_excel(xls_path, sheet_name=0)
    
    print(f"Loaded {len(df)} entries")
    print(f"\nColumns found: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Save raw data for inspection
    raw_output = str(output_csv).replace('.csv', '_raw.csv')
    df.to_csv(raw_output, index=False)
    print(f"\nSaved raw data to {raw_output}")
    
    # Extract key information
    # Common column names in ASBench (may need adjustment based on actual structure)
    column_mapping = {
        'PDB ID': ['PDB ID', 'PDB_ID', 'pdb_id', 'PDB', 'PDBid'],
        'Chain ID': ['Chain ID', 'Chain_ID', 'chain_id', 'Chain', 'chain'],
        'Residue IDs': ['Residue ID (PDB)', 'Residue_ID', 'residue_id', 'Allosteric Site Residues', 'Residues'],
        'Protein Name': ['Protein Name', 'Protein_Name', 'protein_name', 'Protein'],
        'Allosteric Site': ['Allosteric Site', 'Allosteric_Site', 'allosteric_site', 'Site']
    }
    
    # Try to find actual column names
    actual_columns = {}
    for key, possible_names in column_mapping.items():
        for col in df.columns:
            if col in possible_names:
                actual_columns[key] = col
                break
    
    print(f"\nMapped columns: {actual_columns}")
    
    # Create structured output
    structured_data = []
    
    for idx, row in df.iterrows():
        entry = {
            'entry_id': idx,
        }
        
        # Add columns we found
        for key, col_name in actual_columns.items():
            entry[key.lower().replace(' ', '_')] = row[col_name]
        
        # Add all other columns for completeness
        for col in df.columns:
            if col not in actual_columns.values():
                entry[col] = row[col]
        
        structured_data.append(entry)
    
    # Create structured DataFrame
    structured_df = pd.DataFrame(structured_data)
    
    # Save structured CSV
    structured_df.to_csv(output_csv, index=False)
    print(f"\nSaved structured data to {output_csv}")
    
    # Print summary statistics
    print(f"\n=== Summary ===")
    if 'pdb_id' in structured_df.columns:
        unique_pdbs = structured_df['pdb_id'].nunique()
        print(f"Unique PDB IDs: {unique_pdbs}")
    
    if 'chain_id' in structured_df.columns:
        print(f"Unique chains: {structured_df['chain_id'].nunique()}")
    
    print(f"Total entries: {len(structured_df)}")
    
    return structured_df


def extract_pdb_list(structured_df, output_txt):
    """
    Extract list of unique PDB IDs for downloading.
    
    Args:
        structured_df: Structured DataFrame from parse_asbench_xls
        output_txt: Output path for PDB list
    """
    if 'pdb_id' in structured_df.columns:
        pdb_ids = structured_df['pdb_id'].unique()
        pdb_ids = [str(pdb).strip().upper() for pdb in pdb_ids if pd.notna(pdb)]
        
        with open(output_txt, 'w') as f:
            for pdb_id in sorted(pdb_ids):
                f.write(f"{pdb_id}\n")
        
        print(f"\nSaved {len(pdb_ids)} unique PDB IDs to {output_txt}")
        return pdb_ids
    else:
        print("Warning: No 'pdb_id' column found")
        return []


def check_existing_pdbs(pdb_ids, pdb_dir):
    """
    Check which PDB files we already have.
    
    Args:
        pdb_ids: List of PDB IDs
        pdb_dir: Directory containing PDB files
    """
    existing = []
    missing = []
    
    for pdb_id in pdb_ids:
        # Check various possible filenames
        possible_names = [
            f"{pdb_id}.pdb",
            f"{pdb_id.lower()}.pdb",
            f"pdb{pdb_id.lower()}.ent",
        ]
        
        found = False
        for filename in possible_names:
            if os.path.exists(os.path.join(pdb_dir, filename)):
                existing.append(pdb_id)
                found = True
                break
        
        # Also check if any file contains this PDB ID
        if not found:
            for file in os.listdir(pdb_dir):
                if pdb_id in file.upper():
                    existing.append(pdb_id)
                    found = True
                    break
        
        if not found:
            missing.append(pdb_id)
    
    print(f"\n=== PDB File Status ===")
    print(f"Already downloaded: {len(existing)}/{len(pdb_ids)}")
    print(f"Missing: {len(missing)}/{len(pdb_ids)}")
    
    if missing:
        print(f"\nMissing PDB IDs: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    
    return existing, missing


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    xls_path = project_root / "data" / "asbench" / "AsBench_Core_Set.xls"
    output_csv = project_root / "data" / "asbench" / "asbench_annotations.csv"
    pdb_list = project_root / "data" / "asbench" / "pdb_list.txt"
    pdb_dir = project_root / "data" / "pdb"
    
    # Check if XLS file exists
    if not xls_path.exists():
        print(f"Error: {xls_path} not found!")
        print("Please download ASBench Core Set from http://mdl.shsmu.edu.cn/ASBench/")
        return 1
    
    # Parse XLS
    structured_df = parse_asbench_xls(xls_path, output_csv)
    
    # Extract PDB list
    pdb_ids = extract_pdb_list(structured_df, pdb_list)
    
    # Check existing PDB files
    if pdb_ids:
        existing, missing = check_existing_pdbs(pdb_ids, pdb_dir)
        
        if missing:
            missing_file = project_root / "data" / "asbench" / "missing_pdbs.txt"
            with open(missing_file, 'w') as f:
                for pdb_id in missing:
                    f.write(f"{pdb_id}\n")
            print(f"\nSaved missing PDB IDs to {missing_file}")
    
    print("\n✓ ASBench parsing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

