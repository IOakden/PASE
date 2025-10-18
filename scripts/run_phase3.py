#!/usr/bin/env python3
"""
Run Phase 3: Preprocessing and Label Generation

This script orchestrates the complete Phase 3 workflow:
1. Parse PDB structures
2. Compute residue features (SASA, depth, secondary structure, coordinates)
3. Generate positive labels (residues near modulators)
4. Generate negative labels (stratified sampling)
5. Save processed dataset

Usage:
    python scripts/run_phase3.py
    python scripts/run_phase3.py --max-proteins 10  # Test on 10 proteins
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
from Bio.PDB import PDBParser

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from preprocessing import compute_residue_features
from labeling import create_label_dataset


def run_phase3(max_proteins: Optional[int] = None):
    """
    Run complete Phase 3 pipeline.
    
    Args:
        max_proteins: Limit processing to first N proteins (for testing)
    """
    # Setup paths
    project_root = Path(__file__).parent.parent
    
    # Input paths
    usable_proteins = project_root / "data" / "processed" / "usable_proteins.txt"
    asbench_csv = project_root / "data" / "asbench" / "asbench_annotations.csv"
    pdb_dir = project_root / "data" / "pdb"
    
    # Output paths
    processed_dir = project_root / "data" / "processed"
    features_dir = processed_dir / "features"
    labels_csv = processed_dir / "labels.csv"
    
    # Create directories
    features_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PHASE 3: PREPROCESSING & LABEL GENERATION")
    print("=" * 70)
    print(f"\nInput:")
    print(f"  Usable proteins: {usable_proteins}")
    print(f"  ASBench CSV: {asbench_csv}")
    print(f"  PDB directory: {pdb_dir}")
    print(f"\nOutput:")
    print(f"  Features: {features_dir}")
    print(f"  Labels: {labels_csv}")
    print("=" * 70)
    
    # Load usable proteins list
    if usable_proteins.exists():
        with open(usable_proteins, 'r') as f:
            usable_pdb_files = [line.strip() for line in f if line.strip()]
        print(f"\nUsing {len(usable_pdb_files)} validated proteins from Phase 2")
        
        # Extract PDB IDs
        usable_pdb_ids = set()
        for filename in usable_pdb_files:
            # Extract PDB ID from filename like AS001000501_3UO9_complex.pdb
            import re
            match = re.search(r'_([A-Z0-9]{4})', filename)
            if match:
                usable_pdb_ids.add(match.group(1))
        
        # Filter annotations
        annotations = pd.read_csv(asbench_csv)
        annotations = annotations[annotations['pdb_id'].isin(usable_pdb_ids)]
        print(f"Filtered to {len(annotations)} annotations")
    else:
        print(f"\nWarning: {usable_proteins} not found, using all annotations")
        annotations = pd.read_csv(asbench_csv)
    
    if max_proteins:
        annotations = annotations.head(max_proteins)
        print(f"Limited to {max_proteins} proteins for testing")
    
    # Step 1: Compute features
    print("\n" + "=" * 70)
    print("STEP 1: COMPUTE RESIDUE FEATURES")
    print("=" * 70)
    
    parser = PDBParser(QUIET=True)
    
    processed_proteins = set()
    
    for idx, row in annotations.iterrows():
        pdb_id = str(row['pdb_id']).strip()
        
        # Skip if already processed this PDB
        if pdb_id in processed_proteins:
            continue
        processed_proteins.add(pdb_id)
        
        features_file = features_dir / f"{pdb_id.lower()}_features.csv"
        
        # Skip if already computed
        if features_file.exists():
            print(f"  [{len(processed_proteins)}/{len(annotations)}] {pdb_id}: Using cached features")
            continue
        
        # Find PDB file
        pdb_path = Path(pdb_dir)
        pdb_files = list(pdb_path.glob(f"*{pdb_id}*complex.pdb"))
        if not pdb_files:
            pdb_files = list(pdb_path.glob(f"*{pdb_id}*.pdb"))
        
        if not pdb_files:
            print(f"  [{len(processed_proteins)}/{len(annotations)}] {pdb_id}: PDB file not found, skipping")
            continue
        
        pdb_file = str(pdb_files[0])
        
        try:
            print(f"  [{len(processed_proteins)}/{len(annotations)}] {pdb_id}: Computing features...", end=" ")
            
            # Parse and compute features
            structure = parser.get_structure(pdb_id, pdb_file)
            features_df = compute_residue_features(pdb_file, structure)
            
            # Save
            features_df.to_csv(features_file, index=False)
            print(f"✓ {len(features_df)} residues")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Step 2: Generate labels
    print("\n" + "=" * 70)
    print("STEP 2: GENERATE LABELS")
    print("=" * 70)
    
    labels_df = create_label_dataset(
        str(asbench_csv),
        str(pdb_dir),
        str(labels_csv),
        features_dir=str(features_dir),
        negative_ratio=negative_ratio,
        exclusion_distance=exclusion_distance
    )
    
    # Final summary
    print("\n" + "=" * 70)
    print("PHASE 3 COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  ✓ Features: {features_dir}/ ({len(list(features_dir.glob('*.csv')))} files)")
    print(f"  ✓ Labels: {labels_csv}")
    
    if len(labels_df) > 0:
        print(f"\nDataset statistics:")
        print(f"  Total labels: {len(labels_df):,}")
        print(f"  Positive (allosteric): {(labels_df['label'] == 1).sum():,}")
        print(f"  Negative (non-allosteric): {(labels_df['label'] == 0).sum():,}")
        print(f"  Unique proteins: {labels_df['pdb_id'].nunique()}")
        pos_count = (labels_df['label'] == 1).sum()
        neg_count = (labels_df['label'] == 0).sum()
        if pos_count > 0:
            print(f"  Ratio: 1:{neg_count / pos_count:.2f}")
    
    print(f"\n{'=' * 70}")
    print("Next steps:")
    print("  1. Inspect labels.csv to verify label distribution")
    print("  2. Review feature files in data/processed/features/")
    print("  3. Proceed to Phase 4: Graph Construction")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Run Phase 3: Preprocessing and Label Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python scripts/run_phase3.py
  
  # Test on first 5 proteins
  python scripts/run_phase3.py --max-proteins 5
        """
    )
    
    parser.add_argument(
        '--max-proteins',
        type=int,
        default=None,
        help='Maximum number of proteins to process (for testing)'
    )
    parser.add_argument(
        '--negative-ratio',
        type=float,
        default=3.0,
        help='Ratio of negative to positive labels (default: 3.0)'
    )
    parser.add_argument(
        '--exclusion-distance',
        type=float,
        default=10.0,
        help='Exclusion distance around allosteric sites in Angstroms (default: 10.0)'
    )
    
    args = parser.parse_args()
    
    # Store in global scope for access in run_phase3
    global negative_ratio, exclusion_distance
    negative_ratio = args.negative_ratio
    exclusion_distance = args.exclusion_distance
    
    run_phase3(max_proteins=args.max_proteins)


if __name__ == "__main__":
    main()

