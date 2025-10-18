"""
PDB parsing and feature computation for Phase 3.

Implements PDB parsing and computes residue-level features including:
- SASA (Solvent Accessible Surface Area)
- Depth (distance from surface)
- Secondary structure (helix/sheet/coil)
- Cα coordinates
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from Bio.PDB import PDBParser, DSSP, PDBIO
from Bio.PDB.SASA import ShrakeRupley
import warnings

warnings.filterwarnings('ignore')


def parse_pdb(pdb_file: str) -> Dict:
    """
    Parse PDB file and extract basic structure information.
    
    Args:
        pdb_file: Path to PDB file
        
    Returns:
        dict with keys:
            - coords: numpy array (N_atoms, 3) of atomic coordinates
            - residues: list of (chain_id, res_num, res_name) tuples
            - atoms: list of (atom_name, element) tuples
            - b_factors: numpy array of B-factors
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)
    
    coords = []
    residues = []
    atoms = []
    b_factors = []
    
    for model in structure:
        for chain in model:
            for residue in chain:
                # Skip HETATM (only process standard amino acids)
                if residue.id[0] != ' ':
                    continue
                
                chain_id = chain.id
                res_num = residue.id[1]
                insertion_code = residue.id[2].strip()
                res_name = residue.resname
                
                # Create residue identifier
                if insertion_code:
                    res_id = f"{res_num}{insertion_code}"
                else:
                    res_id = str(res_num)
                
                # Store residue info once per residue
                if (chain_id, res_id, res_name) not in residues:
                    residues.append((chain_id, res_id, res_name))
                
                # Store all atoms
                for atom in residue:
                    coords.append(atom.coord)
                    atoms.append((atom.name, atom.element))
                    b_factors.append(atom.bfactor)
    
    return {
        'coords': np.array(coords),
        'residues': residues,
        'atoms': atoms,
        'b_factors': np.array(b_factors)
    }


def compute_sasa(structure):
    """
    Compute Solvent Accessible Surface Area for all residues.
    
    Args:
        structure: Biopython Structure object
        
    Returns:
        dict mapping (chain_id, res_num) to SASA value
    """
    sr = ShrakeRupley()
    sr.compute(structure, level="R")  # Residue-level
    
    sasa_dict = {}
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != ' ':
                    continue
                
                chain_id = chain.id
                res_num = residue.id[1]
                insertion_code = residue.id[2].strip()
                
                if insertion_code:
                    res_id = f"{res_num}{insertion_code}"
                else:
                    res_id = str(res_num)
                
                sasa_dict[(chain_id, res_id)] = residue.sasa
    
    return sasa_dict


def compute_depth(structure):
    """
    Compute depth (distance from surface) for all residues.
    
    Approximated as inverse of SASA for simplicity.
    More sophisticated: use Bio.PDB.ResidueDepth (requires MSMS)
    
    Args:
        structure: Biopython Structure object
        
    Returns:
        dict mapping (chain_id, res_num) to depth value
    """
    # Compute SASA first
    sasa_dict = compute_sasa(structure)
    
    # Depth approximation: high SASA = low depth (surface)
    # Normalize and invert
    if not sasa_dict:
        return {}
    
    max_sasa = max(sasa_dict.values()) if sasa_dict.values() else 1.0
    
    depth_dict = {}
    for key, sasa in sasa_dict.items():
        # Normalize SASA to 0-1, then invert
        normalized_sasa = sasa / max_sasa if max_sasa > 0 else 0
        depth = 1.0 - normalized_sasa  # High SASA -> low depth
        depth_dict[key] = depth
    
    return depth_dict


def compute_secondary_structure(pdb_file: str, structure) -> Dict:
    """
    Compute secondary structure using DSSP.
    
    Args:
        pdb_file: Path to PDB file (needed for DSSP)
        structure: Biopython Structure object
        
    Returns:
        dict mapping (chain_id, res_num) to secondary structure code
        Codes: H=helix, E=sheet, C=coil
    """
    ss_dict = {}
    
    try:
        model = structure[0]
        dssp = DSSP(model, pdb_file, dssp='mkdssp')
        
        for key in dssp:
            chain_id = key[0]
            res_id = key[1]
            
            # Get DSSP output
            ss_code = dssp[key][2]  # Secondary structure code
            
            # Simplify to H/E/C
            if ss_code in ['H', 'G', 'I']:  # Alpha helix, 3-10 helix, Pi helix
                simplified = 'H'
            elif ss_code in ['E', 'B']:  # Beta sheet, Beta bridge
                simplified = 'E'
            else:  # Coil/loop
                simplified = 'C'
            
            # Format residue ID
            res_num = res_id[1]
            insertion_code = res_id[2].strip()
            if insertion_code:
                res_key = f"{res_num}{insertion_code}"
            else:
                res_key = str(res_num)
            
            ss_dict[(chain_id, res_key)] = simplified
            
    except Exception as e:
        # DSSP not available or error
        print(f"    Warning: DSSP failed ({e}), using default 'C' for all")
        # Fall back to coil for all residues
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.id[0] == ' ':
                        chain_id = chain.id
                        res_num = residue.id[1]
                        insertion_code = residue.id[2].strip()
                        if insertion_code:
                            res_key = f"{res_num}{insertion_code}"
                        else:
                            res_key = str(res_num)
                        ss_dict[(chain_id, res_key)] = 'C'
    
    return ss_dict


def get_ca_coordinates(structure) -> Dict:
    """
    Get Cα (C-alpha) coordinates for all residues.
    
    Args:
        structure: Biopython Structure object
        
    Returns:
        dict mapping (chain_id, res_num) to (x, y, z) coordinates
    """
    ca_coords = {}
    
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != ' ':
                    continue
                
                # Get CA atom
                if 'CA' in residue:
                    ca_atom = residue['CA']
                    chain_id = chain.id
                    res_num = residue.id[1]
                    insertion_code = residue.id[2].strip()
                    
                    if insertion_code:
                        res_key = f"{res_num}{insertion_code}"
                    else:
                        res_key = str(res_num)
                    
                    ca_coords[(chain_id, res_key)] = tuple(ca_atom.coord)
    
    return ca_coords


def compute_residue_features(pdb_file: str, structure=None) -> pd.DataFrame:
    """
    Compute comprehensive residue-level features.
    
    Args:
        pdb_file: Path to PDB file
        structure: Biopython Structure object (optional, will parse if not provided)
        
    Returns:
        DataFrame with columns:
            - chain_id: chain identifier
            - res_num: residue number (as string, may include insertion code)
            - res_name: three-letter residue name
            - sasa: solvent accessible surface area
            - depth: approximate depth from surface
            - secondary_structure: H/E/C (helix/sheet/coil)
            - ca_x, ca_y, ca_z: Cα coordinates
    """
    # Parse structure if not provided
    if structure is None:
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
    
    # Get residue list
    residues = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] == ' ':  # Standard amino acid
                    chain_id = chain.id
                    res_num = residue.id[1]
                    insertion_code = residue.id[2].strip()
                    res_name = residue.resname
                    
                    if insertion_code:
                        res_key = f"{res_num}{insertion_code}"
                    else:
                        res_key = str(res_num)
                    
                    residues.append({
                        'chain_id': chain_id,
                        'res_num': res_key,
                        'res_name': res_name
                    })
    
    # Compute features
    sasa_dict = compute_sasa(structure)
    depth_dict = compute_depth(structure)
    ss_dict = compute_secondary_structure(pdb_file, structure)
    ca_dict = get_ca_coordinates(structure)
    
    # Build DataFrame
    features = []
    for res_info in residues:
        chain_id = res_info['chain_id']
        res_num = res_info['res_num']
        res_name = res_info['res_name']
        
        key = (chain_id, res_num)
        
        # Get CA coordinates
        ca_coords = ca_dict.get(key, (np.nan, np.nan, np.nan))
        
        features.append({
            'chain_id': chain_id,
            'res_num': res_num,
            'res_name': res_name,
            'sasa': sasa_dict.get(key, 0.0),
            'depth': depth_dict.get(key, 0.5),
            'secondary_structure': ss_dict.get(key, 'C'),
            'ca_x': ca_coords[0],
            'ca_y': ca_coords[1],
            'ca_z': ca_coords[2]
        })
    
    return pd.DataFrame(features)

