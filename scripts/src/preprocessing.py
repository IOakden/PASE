"""
Complete Phase 3 pipeline: Preprocessing and label generation.

This script runs the entire Phase 3 workflow:
1. Generate quality report
2. Compute features for all PDB files
3. Generate labels (positive + negative)
4. Save processed dataset

Usage:
    python scripts/run_phase3.py [--skip-quality] [--skip-features]
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_quality import generate_quality_report, check_pdb_quality
from preprocessing import compute_residue_features, parse_pdb
from labeling import create_label_dataset
from Bio.PDB import PDBParser


def run_phase3(
    skip_quality: bool = False,
    skip_features: bool = False,
    max_proteins: int = None
):
    """
    Run complete Phase 3 pipeline.
    
    Args:
        skip_quality: Skip quality report generation
        skip_features: Skip feature computation (use existing if available)
        max_proteins: Limit processing to first N proteins (for testing)
    """
    # Setup paths
    project_root = Path(__file__).parent.parent
    
    # Input paths
    asbench_csv = project_root / "data" / "asbench" / "asbench_annotations.csv"
    pdb_dir = project_root / "data" / "pdb"
    
    # Output paths
    processed_dir = project_root / "data" / "processed"
    features_dir = processed_dir / "features"
    quality_report = processed_dir / "quality_report.csv"
    labels_csv = processed_dir / "labels.csv"
    
    # Create directories
    processed_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("PHASE 3: PREPROCESSING & LABEL GENERATION")
    print("="*70)
    print(f"\nInput:")
    print(f"  ASBench CSV: {asbench_csv}")
    print(f"  PDB directory: {pdb_dir}")
    print(f"\nOutput:")
    print(f"  Quality report: {quality_report}")
    print(f"  Features: {features_dir}")
    print(f"  Labels: {labels_csv}")
    print("="*70)
    
    # Step 1: Generate quality report
    if not skip_quality:
        print("\n" + "="*70)
        print("STEP 1: DATA QUALITY REPORT")
        print("="*70)
        
        report_df = generate_quality_report(
            str(asbench_csv),
            str(pdb_dir),
            str(quality_report)
        )
        
        # Filter to good quality proteins
        good_quality = report_df[report_df['exclude'] == False]
        print(f"\n✓ Found {len(good_quality)} good quality proteins")
        
        if max_proteins:
            good_quality = good_quality.head(max_proteins)
            print(f"  (Limited to {max_proteins} for testing)")
    else:
        print("\n⊘ Skipping quality report (using existing)")
        if quality_report.exists():
            report_df = pd.read_csv(quality_report)
            good_quality = report_df[report_df['exclude'] == False]
            if max_proteins:
                good_quality = good_quality.head(max_proteins)
        else:
            print("  Warning: No quality report found, processing all proteins")
            report_df = pd.read_csv(asbench_csv)
            good_quality = report_df
            if max_proteins:
                good_quality = good_quality.head(max_proteins)
    
    # Step 2: Compute features
    if not skip_features:
        print("\n" + "="*70)
        print("STEP 2: COMPUTE RESIDUE FEATURES")
        print("="*70)
        
        parser = PDBParser(QUIET=True)
        
        for idx, row in good_quality.iterrows():
            pdb_id = str(row.get('pdb_id', '')).strip().lower()
            if not pdb_id:
                continue
            
            features_file = features_dir / f"{pdb_id}_features.csv"
            
            # Skip if already computed
            if features_file.exists():
                print(f"[{idx+1}/{len(good_quality)}] {pdb_id.upper()}: Using cached features")
                continue
            
            # Find PDB file
            pdb_file = None
            for ext in ['.pdb', '.ent']:
                candidates = [
                    pdb_dir / f"{pdb_id}{ext}",
                    pdb_dir / f"{pdb_id.upper()}{ext}",
                    pdb_dir / f"pdb{pdb_id}{ext}",
                ]
                for candidate in candidates:
                    if candidate.exists():
                        pdb_file = candidate
                        break
                if pdb_file:
                    break
            
            if not pdb_file:
                print(f"[{idx+1}/{len(good_quality)}] {pdb_id.upper()}: PDB file not found, skipping")
                continue
            
            try:
                print(f"[{idx+1}/{len(good_quality)}] {pdb_id.upper()}: Computing features...")
                
                # Parse and compute features
                structure = parser.get_structure(pdb_id, str(pdb_file))
                features_df = compute_residue_features(str(pdb_file), structure)
                
                # Save
                features_df.to_csv(features_file, index=False)
                print(f"  ✓ Saved {len(features_df)} residues")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
    else:
        print("\n⊘ Skipping feature computation (using existing)")
    
    # Step 3: Generate labels
    print("\n" + "="*70)
    print("STEP 3: GENERATE LABELS")
    print("="*70)
    
    # Filter ASBench to only good quality proteins
    if not skip_quality and quality_report.exists():
        report_df = pd.read_csv(quality_report)
        good_pdb_ids = set(report_df[report_df['exclude'] == False]['pdb_id'].str.lower())
        asbench_full = pd.read_csv(asbench_csv)
        asbench_filtered = asbench_full[asbench_full['pdb_id'].str.lower().isin(good_pdb_ids)]
        
        if max_proteins:
            asbench_filtered = asbench_filtered.head(max_proteins)
        
        # Save filtered annotations
        filtered_csv = processed_dir / "asbench_filtered.csv"
        asbench_filtered.to_csv(filtered_csv, index=False)
        print(f"Using {len(asbench_filtered)} filtered proteins")
        
        input_csv = filtered_csv
    else:
        input_csv = asbench_csv
    
    labels_df = create_label_dataset(
        str(input_csv),
        str(pdb_dir),
        str(labels_csv),
        features_dir=str(features_dir),
        negative_ratio=3.0,
        exclusion_distance=10.0
    )
    
    # Final summary
    print("\n" + "="*70)
    print("PHASE 3 COMPLETE!")
    print("="*70)
    print(f"\nGenerated files:")
    if not skip_quality:
        print(f"  ✓ Quality report: {quality_report}")
    print(f"  ✓ Features: {features_dir}/ ({len(list(features_dir.glob('*.csv')))} files)")
    print(f"  ✓ Labels: {labels_csv}")
    
    print(f"\nDataset statistics:")
    print(f"  Total labels: {len(labels_df)}")
    print(f"  Positive (allosteric): {(labels_df['label'] == 1).sum()}")
    print(f"  Negative (non-allosteric): {(labels_df['label'] == 0).sum()}")
    print(f"  Unique proteins: {labels_df['pdb_id'].nunique()}")
    print(f"  Ratio: 1:{(labels_df['label'] == 0).sum() / max(1, (labels_df['label'] == 1).sum()):.2f}")
    
    print(f"\n{'='*70}")
    print("Next steps:")
    print("  1. Review quality_report.csv to check data quality")
    print("  2. Inspect labels.csv to verify label distribution")
    print("  3. Proceed to Phase 4: Graph Construction")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Run Phase 3: Preprocessing and Label Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python scripts/run_phase3.py
  
  # Skip quality report (use existing)
  python scripts/run_phase3.py --skip-quality
  
  # Test on first 5 proteins
  python scripts/run_phase3.py --max-proteins 5
  
  # Use cached features
  python scripts/run_phase3.py --skip-features
        """
    )
    
    parser.add_argument('--skip-quality', action='store_true',
                       help='Skip quality report generation')
    parser.add_argument('--skip-features', action='store_true',
                       help='Skip feature computation (use existing)')
    parser.add_argument('--max-proteins', type=int, default=None,
                       help='Maximum number of proteins to process (for testing)')
    
    args = parser.parse_args()
    
    run_phase3(
        skip_quality=args.skip_quality,
        skip_features=args.skip_features,
        max_proteins=args.max_proteins
    )


if __name__ == "__main__":
    main()