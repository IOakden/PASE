#!/usr/bin/env python3
"""
Download PDB structures from RCSB.

PURPOSE:
  Utility script to download clean PDB files directly from RCSB PDB database.
  This is NOT required for the current project since ASBench includes all PDB files.

USE CASES:
  1. Download clean PDB files without ASBench naming prefix
  2. Get updated/revised structures from RCSB
  3. Work with custom protein lists beyond ASBench
  4. Re-download if files become corrupted

CURRENT WORKFLOW:
  We copied PDB files directly from ASBench distribution:
    ASBench provides: AS001000501_3UO9.pdb (with site ID prefix)
    This script gets: 3UO9.pdb (clean PDB ID only)
  
  Both formats work fine - this script is optional infrastructure.
"""

import os
import sys
from pathlib import Path
from Bio.PDB import PDBList


def download_pdbs_from_list(pdb_list_file, output_dir, overwrite=False):
    """
    Download PDB structures from a list of PDB IDs.
    
    Args:
        pdb_list_file: File containing PDB IDs (one per line)
        output_dir: Directory to save PDB files
        overwrite: Whether to re-download existing files
    """
    # Read PDB list
    with open(pdb_list_file, 'r') as f:
        pdb_ids = [line.strip().upper() for line in f if line.strip()]
    
    print(f"Found {len(pdb_ids)} PDB IDs to download")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize PDB downloader
    pdbl = PDBList()
    
    downloaded = []
    skipped = []
    failed = []
    
    for i, pdb_id in enumerate(pdb_ids, 1):
        print(f"\n[{i}/{len(pdb_ids)}] Processing {pdb_id}...", end=" ")
        
        # Check if file already exists
        existing_files = [
            os.path.join(output_dir, f"{pdb_id}.pdb"),
            os.path.join(output_dir, f"{pdb_id.lower()}.pdb"),
            os.path.join(output_dir, f"pdb{pdb_id.lower()}.ent"),
        ]
        
        if any(os.path.exists(f) for f in existing_files) and not overwrite:
            print("Already exists, skipping")
            skipped.append(pdb_id)
            continue
        
        try:
            # Download PDB file
            # pdb_format='pdb' for older format, 'mmCif' for newer
            filename = pdbl.retrieve_pdb_file(
                pdb_id,
                pdir=output_dir,
                file_format='pdb',
                overwrite=overwrite
            )
            print(f"Downloaded: {filename}")
            downloaded.append(pdb_id)
        except Exception as e:
            print(f"Failed: {e}")
            failed.append(pdb_id)
    
    # Print summary
    print("\n" + "="*60)
    print("Download Summary")
    print("="*60)
    print(f"Downloaded: {len(downloaded)}")
    print(f"Skipped (already exist): {len(skipped)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed PDB IDs:")
        for pdb_id in failed:
            print(f"  - {pdb_id}")
        
        # Save failed IDs to file
        failed_file = Path(pdb_list_file).parent / "failed_downloads.txt"
        with open(failed_file, 'w') as f:
            for pdb_id in failed:
                f.write(f"{pdb_id}\n")
        print(f"\nSaved failed PDB IDs to {failed_file}")
    
    return downloaded, skipped, failed


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download PDB structures")
    parser.add_argument(
        "--pdb-list",
        default="data/asbench/pdb_list.txt",
        help="File containing PDB IDs to download"
    )
    parser.add_argument(
        "--output-dir",
        default="data/pdb",
        help="Output directory for PDB files"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download existing files"
    )
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    project_root = Path(__file__).parent.parent
    pdb_list = project_root / args.pdb_list
    output_dir = project_root / args.output_dir
    
    if not pdb_list.exists():
        print(f"Error: PDB list file not found: {pdb_list}")
        return 1
    
    print(f"PDB list: {pdb_list}")
    print(f"Output directory: {output_dir}")
    print(f"Overwrite existing: {args.overwrite}\n")
    
    downloaded, skipped, failed = download_pdbs_from_list(
        pdb_list, output_dir, args.overwrite
    )
    
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

