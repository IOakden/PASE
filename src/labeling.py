"""
Label generation for allosteric site prediction.

Generates positive labels (allosteric residues) based on proximity to modulator,
and negative labels (non-allosteric) using stratified sampling.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Set, Optional
from Bio.PDB import PDBParser, NeighborSearch
import warnings

warnings.filterwarnings('ignore')


def find_modulator_residue(structure, chain_id: str, modulator_res_id: str):
    """
    Find modulator (HETATM) residue in structure.
    
    Args:
        structure: Biopython Structure object
        chain_id: Chain containing modulator
        modulator_res_id: Residue ID of modulator
        
    Returns:
        Modulator residue object, or None if not found
    """
    for model in structure:
        for chain in model:
            if chain.id != chain_id:
                continue
            
            for residue in chain:
                # HETATM residues have non-blank hetero flag
                if residue.id[0] != ' ':
                    res_num = residue.id[1]
                    if str(res_num) == str(modulator_res_id):
                        return residue
    
    return None


def generate_positive_labels(
    pdb_file: str,
    chain_id: str,
    modulator_res_id: str,
    distance_cutoff: float = 5.0
) -> List[Tuple[str, str]]:
    """
    Generate positive labels (allosteric residues) based on proximity to modulator.
    
    Allosteric site residues are defined as protein residues within distance_cutoff
    of the bound modulator molecule.
    
    Args:
        pdb_file: Path to PDB file (protein-modulator complex)
        chain_id: Chain ID containing modulator
        modulator_res_id: Residue ID of modulator (from ASBench)
        distance_cutoff: Distance threshold in Angstroms (default: 5.0)
        
    Returns:
        List of (chain_id, res_num) tuples for allosteric residues
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)
    
    # Find modulator
    modulator = find_modulator_residue(structure, chain_id, modulator_res_id)
    if not modulator:
        return []
    
    # Get all protein atoms
    atom_list = []
    residue_map = {}
    
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] == ' ':  # Standard amino acid only
                    for atom in residue:
                        atom_list.append(atom)
                        residue_map[atom] = residue
    
    if not atom_list:
        return []
    
    # Build neighbor search
    ns = NeighborSearch(atom_list)
    
    # Find residues with atoms near modulator
    allosteric_residues = set()
    
    for mod_atom in modulator:
        nearby_atoms = ns.search(mod_atom.coord, distance_cutoff)
        for atom in nearby_atoms:
            if atom in residue_map:
                res = residue_map[atom]
                res_chain_id = res.parent.id
                res_num = res.id[1]
                insertion_code = res.id[2].strip()
                
                if insertion_code:
                    res_id = f"{res_num}{insertion_code}"
                else:
                    res_id = str(res_num)
                
                allosteric_residues.add((res_chain_id, res_id))
    
    return list(allosteric_residues)


def generate_negative_labels(
    pdb_file: str,
    positive_labels: List[Tuple[str, str]],
    features_df: Optional[pd.DataFrame] = None,
    negative_ratio: float = 3.0,
    exclusion_distance: float = 10.0
) -> List[Tuple[str, str]]:
    """
    Generate negative labels (non-allosteric residues) using stratified sampling.
    
    Excludes:
    - Residues within exclusion_distance of any allosteric residue
    - Active sites (if available, not implemented yet)
    
    Samples negatives stratified by:
    - Surface exposed (high SASA)
    - Buried (low SASA)
    - Secondary structure
    
    Args:
        pdb_file: Path to PDB file
        positive_labels: List of (chain_id, res_num) tuples for allosteric residues
        features_df: DataFrame with features (optional, will compute if not provided)
        negative_ratio: Ratio of negative to positive labels
        exclusion_distance: Distance in Angstroms to exclude around allosteric sites
        
    Returns:
        List of (chain_id, res_num) tuples for negative residues
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)
    
    # Get all protein residues
    all_residues = []
    residue_objects = {}
    
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] == ' ':
                    chain_id = chain.id
                    res_num = residue.id[1]
                    insertion_code = residue.id[2].strip()
                    
                    if insertion_code:
                        res_id = f"{res_num}{insertion_code}"
                    else:
                        res_id = str(res_num)
                    
                    key = (chain_id, res_id)
                    all_residues.append(key)
                    residue_objects[key] = residue
    
    # Get CA coordinates for allosteric residues
    allosteric_ca_coords = []
    for chain_id, res_id in positive_labels:
        key = (chain_id, res_id)
        if key in residue_objects:
            res = residue_objects[key]
            if 'CA' in res:
                allosteric_ca_coords.append(res['CA'].coord)
    
    allosteric_ca_coords = np.array(allosteric_ca_coords)
    
    # Exclude residues within exclusion_distance of allosteric sites
    candidate_negatives = []
    
    for key in all_residues:
        # Skip if it's a positive label
        if key in positive_labels:
            continue
        
        # Check distance to nearest allosteric residue
        if key in residue_objects and 'CA' in residue_objects[key]:
            ca_coord = residue_objects[key]['CA'].coord
            
            if len(allosteric_ca_coords) > 0:
                # Calculate distance to nearest allosteric residue
                distances = np.linalg.norm(allosteric_ca_coords - ca_coord, axis=1)
                min_distance = np.min(distances)
                
                if min_distance > exclusion_distance:
                    candidate_negatives.append(key)
            else:
                candidate_negatives.append(key)
    
    # Calculate number of negatives to sample
    num_to_sample = int(len(positive_labels) * negative_ratio)
    
    if len(candidate_negatives) == 0:
        return []
    
    # If features available, do stratified sampling
    if features_df is not None:
        # Merge features with candidates
        candidates_with_features = []
        for chain_id, res_id in candidate_negatives:
            feat_row = features_df[
                (features_df['chain_id'] == chain_id) & 
                (features_df['res_num'] == res_id)
            ]
            if not feat_row.empty:
                sasa = feat_row.iloc[0]['sasa']
                ss = feat_row.iloc[0]['secondary_structure']
                candidates_with_features.append({
                    'chain_id': chain_id,
                    'res_num': res_id,
                    'sasa': sasa,
                    'ss': ss
                })
        
        if len(candidates_with_features) > 0:
            cand_df = pd.DataFrame(candidates_with_features)
            
            # Define thresholds (these are approximate)
            surface_samples = int(num_to_sample * 0.4)
            buried_samples = int(num_to_sample * 0.4)
            intermediate_samples = num_to_sample - surface_samples - buried_samples
            
            surface = cand_df[cand_df['sasa'] > 20.0]
            buried = cand_df[cand_df['sasa'] < 5.0]
            intermediate = cand_df[(cand_df['sasa'] >= 5.0) & (cand_df['sasa'] <= 20.0)]
            
            # Sample from each stratum
            sampled = []
            
            if len(surface) > 0:
                n = min(surface_samples, len(surface))
                sampled.append(surface.sample(n=n, random_state=42))
            
            if len(buried) > 0:
                n = min(buried_samples, len(buried))
                sampled.append(buried.sample(n=n, random_state=42))
            
            if len(intermediate) > 0:
                n = min(intermediate_samples, len(intermediate))
                sampled.append(intermediate.sample(n=n, random_state=42))
            
            if sampled:
                sampled_df = pd.concat(sampled)
                negative_labels = [(row['chain_id'], row['res_num']) for _, row in sampled_df.iterrows()]
                return negative_labels
    
    # Fallback: random sample without stratification
    indices = np.random.choice(
        len(candidate_negatives),
        size=min(num_to_sample, len(candidate_negatives)),
        replace=False
    )
    negative_labels = [candidate_negatives[i] for i in indices]
    
    return negative_labels


def create_label_dataset(
    annotations_csv: str,
    pdb_dir: str,
    output_csv: str,
    features_dir: Optional[str] = None,
    negative_ratio: float = 3.0,
    exclusion_distance: float = 10.0
) -> pd.DataFrame:
    """
    Create complete labeled dataset for training.
    
    Args:
        annotations_csv: Path to ASBench annotations CSV
        pdb_dir: Directory containing PDB files
        output_csv: Output path for labels CSV
        features_dir: Directory with pre-computed features (optional)
        negative_ratio: Ratio of negative to positive labels
        exclusion_distance: Distance to exclude around allosteric sites
        
    Returns:
        DataFrame with columns: pdb_id, chain_id, res_num, label (0/1)
    """
    # Load annotations
    annotations = pd.read_csv(annotations_csv)
    
    all_labels = []
    
    print(f"Generating labels for {len(annotations)} entries...")
    
    for idx, row in annotations.iterrows():
        pdb_id = str(row['pdb_id']).strip()
        chain_id = str(row['chain_id']).strip()
        modulator_res_id = str(row['residue_ids']).strip()
        
        print(f"  [{idx+1}/{len(annotations)}] {pdb_id} (chain {chain_id})...", end=" ")
        
        # Find PDB file (handle ASBench naming with complex suffix)
        pdb_path = Path(pdb_dir)
        pdb_files = list(pdb_path.glob(f"*{pdb_id}*complex.pdb"))
        
        if not pdb_files:
            # Try without complex suffix
            pdb_files = list(pdb_path.glob(f"*{pdb_id}*.pdb"))
        
        if not pdb_files:
            print(f"PDB file not found, skipping")
            continue
        
        pdb_file = str(pdb_files[0])
        
        # Load features if available
        features_df = None
        if features_dir:
            features_path = Path(features_dir) / f"{pdb_id.lower()}_features.csv"
            if features_path.exists():
                features_df = pd.read_csv(features_path)
        
        try:
            # Generate positive labels
            positive = generate_positive_labels(
                pdb_file,
                chain_id,
                modulator_res_id,
                distance_cutoff=5.0
            )
            
            if not positive:
                print(f"No allosteric residues found, skipping")
                continue
            
            # Generate negative labels
            negative = generate_negative_labels(
                pdb_file,
                positive,
                features_df=features_df,
                negative_ratio=negative_ratio,
                exclusion_distance=exclusion_distance
            )
            
            # Add to dataset
            for chain, res_num in positive:
                all_labels.append({
                    'pdb_id': pdb_id,
                    'chain_id': chain,
                    'res_num': res_num,
                    'label': 1
                })
            
            for chain, res_num in negative:
                all_labels.append({
                    'pdb_id': pdb_id,
                    'chain_id': chain,
                    'res_num': res_num,
                    'label': 0
                })
            
            print(f"✓ {len(positive)} positive, {len(negative)} negative")
            
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # Create DataFrame
    labels_df = pd.DataFrame(all_labels)
    
    # Save
    labels_df.to_csv(output_csv, index=False)
    print(f"\n✓ Saved labels to {output_csv}")
    print(f"  Total: {len(labels_df)} labels")
    
    if len(labels_df) > 0 and 'label' in labels_df.columns:
        print(f"  Positive: {(labels_df['label'] == 1).sum()}")
        print(f"  Negative: {(labels_df['label'] == 0).sum()}")
        print(f"  Unique proteins: {labels_df['pdb_id'].nunique()}")
    else:
        print(f"  Warning: No labels generated")
    
    return labels_df

