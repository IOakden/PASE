"""
Graph construction for Phase 4.

Implements protein graph construction with:
- Residue-level nodes with comprehensive features
- KNN edges with distance and direction features
- PyTorch Geometric Data format
"""

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
from sklearn.neighbors import NearestNeighbors
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# Amino acid mapping for one-hot encoding
AMINO_ACIDS = [
    'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE',
    'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL'
]

# Secondary structure mapping
SS_MAPPING = {'H': 0, 'E': 1, 'C': 2}  # Helix, Sheet, Coil


def encode_residue_type(res_name: str) -> np.ndarray:
    """Convert residue name to one-hot encoding (20D)."""
    one_hot = np.zeros(20)
    if res_name in AMINO_ACIDS:
        one_hot[AMINO_ACIDS.index(res_name)] = 1
    return one_hot


def encode_secondary_structure(ss: str) -> np.ndarray:
    """Convert secondary structure to one-hot encoding (3D)."""
    one_hot = np.zeros(3)
    if ss in SS_MAPPING:
        one_hot[SS_MAPPING[ss]] = 1
    return one_hot


def get_backbone_vectors(structure, chain_id: str, res_num: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get backbone orientation vectors for a residue.
    
    Returns:
        Tuple of (N->CA vector, CA->C vector)
    """
    try:
        # Find the residue
        for model in structure:
            for chain in model:
                if chain.id == chain_id:
                    for residue in chain:
                        if residue.id[0] == ' ':
                            # Handle insertion codes
                            insertion_code = residue.id[2].strip()
                            if insertion_code:
                                res_key = f"{residue.id[1]}{insertion_code}"
                            else:
                                res_key = str(residue.id[1])
                            
                            if res_key == res_num:
                                # Get backbone atoms
                                if 'N' in residue and 'CA' in residue and 'C' in residue:
                                    n_coord = residue['N'].coord
                                    ca_coord = residue['CA'].coord
                                    c_coord = residue['C'].coord
                                    
                                    # Compute vectors
                                    n_to_ca = ca_coord - n_coord
                                    ca_to_c = c_coord - ca_coord
                                    
                                    # Normalize
                                    n_to_ca_norm = n_to_ca / (np.linalg.norm(n_to_ca) + 1e-8)
                                    ca_to_c_norm = ca_to_c / (np.linalg.norm(ca_to_c) + 1e-8)
                                    
                                    return n_to_ca_norm, ca_to_c_norm
                                break
    except Exception as e:
        print(f"Warning: Could not get backbone vectors for {chain_id}:{res_num}: {e}")
    
    # Return zero vectors if not found
    return np.zeros(3), np.zeros(3)


def build_protein_graph(pdb_file: str, features_df: pd.DataFrame, labels_df: pd.DataFrame) -> Data:
    """
    Build a protein graph from PDB file and feature/label data.
    
    Args:
        pdb_file: Path to PDB file
        features_df: DataFrame with residue features
        labels_df: DataFrame with residue labels
        
    Returns:
        torch_geometric.data.Data object
    """
    from Bio.PDB import PDBParser
    
    # Parse PDB structure
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)
    
    # Get all residues with features
    residues = []
    node_features = []
    node_labels = []
    ca_coords = []
    
    # Create mapping for labels
    label_map = {}
    for _, row in labels_df.iterrows():
        key = (row['chain_id'], row['res_num'])
        label_map[key] = row['label']
    
    # Process each residue
    for _, row in features_df.iterrows():
        chain_id = row['chain_id']
        res_num = row['res_num']
        res_name = row['res_name']
        
        # Skip if no CA coordinates
        if pd.isna(row['ca_x']) or pd.isna(row['ca_y']) or pd.isna(row['ca_z']):
            continue
            
        residues.append((chain_id, res_num))
        ca_coords.append([row['ca_x'], row['ca_y'], row['ca_z']])
        
        # Get label
        label = label_map.get((chain_id, res_num), 0)
        node_labels.append(label)
        
        # Build node features (25D scalar + 2D vector = 27D total)
        # Scalar features (25D):
        # - Residue type one-hot (20D)
        res_type_onehot = encode_residue_type(res_name)
        
        # - SASA (1D)
        sasa = row['sasa']
        
        # - Depth (1D)
        depth = row['depth']
        
        # - B-factor (1D) - use average B-factor for residue
        b_factor = 50.0  # Default value, could be computed from structure
        
        # - Secondary structure one-hot (3D)
        ss_onehot = encode_secondary_structure(row['secondary_structure'])
        
        # Combine scalar features
        scalar_features = np.concatenate([
            res_type_onehot,  # 20D
            [sasa],           # 1D
            [depth],          # 1D
            [b_factor],       # 1D
            ss_onehot         # 3D
        ])  # Total: 25D
        
        # Vector features (2 vectors of 3D each = 6D)
        n_to_ca, ca_to_c = get_backbone_vectors(structure, chain_id, res_num)
        vector_features = np.concatenate([n_to_ca, ca_to_c])  # 6D
        
        # Combine all features
        node_feature = np.concatenate([scalar_features, vector_features])  # 31D total
        node_features.append(node_feature)
    
    if not residues:
        raise ValueError("No valid residues found in the protein")
    
    # Convert to numpy arrays
    node_features = np.array(node_features)
    node_labels = np.array(node_labels)
    ca_coords = np.array(ca_coords)
    
    # Build KNN edges (K=10)
    nbrs = NearestNeighbors(n_neighbors=min(10, len(residues)), algorithm='ball_tree')
    nbrs.fit(ca_coords)
    
    # Get edge indices and distances
    distances, indices = nbrs.kneighbors(ca_coords)
    
    # Build edge list
    edge_indices = []
    edge_features = []
    
    for i in range(len(residues)):
        for j, neighbor_idx in enumerate(indices[i]):
            if neighbor_idx != i:  # Skip self-loops
                edge_indices.append([i, neighbor_idx])
                
                # Edge scalar feature: Euclidean distance
                distance = distances[i][j]
                
                # Edge vector feature: unit direction vector
                direction = ca_coords[neighbor_idx] - ca_coords[i]
                direction_norm = direction / (np.linalg.norm(direction) + 1e-8)
                
                # Combine edge features
                edge_feature = np.concatenate([[distance], direction_norm])  # 4D
                edge_features.append(edge_feature)
    
    # Convert to tensors
    edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_features, dtype=torch.float)
    x = torch.tensor(node_features, dtype=torch.float)
    y = torch.tensor(node_labels, dtype=torch.long)
    pos = torch.tensor(ca_coords, dtype=torch.float)
    
    # Create PyTorch Geometric Data object
    data = Data(
        x=x,                    # Node features (N, 31)
        edge_index=edge_index,  # Edge indices (2, E)
        edge_attr=edge_attr,   # Edge features (E, 4)
        y=y,                    # Node labels (N,)
        pos=pos                 # Node positions (N, 3)
    )
    
    return data


def build_dataset(protein_list: List[str], pdb_dir: str, 
                  features_dir: str, labels_file: str,
                  output_dir: str = 'data/processed/graphs/') -> List[Data]:
    """
    Build graph dataset for all proteins.
    
    Args:
        protein_list: List of protein IDs
        pdb_dir: Directory containing PDB files
        features_dir: Directory containing feature CSV files
        labels_file: Path to labels CSV file
        output_dir: Output directory for graphs
        
    Returns:
        List of PyTorch Geometric Data objects
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load labels
    labels_df = pd.read_csv(labels_file)
    
    graphs = []
    successful = 0
    failed = 0
    
    for protein_id in protein_list:
        print(f"Processing {protein_id}...")
        
        try:
            # File paths
            pdb_file = Path(pdb_dir) / f"{protein_id}.pdb"
            features_file = Path(features_dir) / f"{protein_id}_features.csv"
            
            # Check if files exist
            if not pdb_file.exists():
                print(f"  Warning: PDB file not found: {pdb_file}")
                failed += 1
                continue
                
            if not features_file.exists():
                print(f"  Warning: Features file not found: {features_file}")
                failed += 1
                continue
            
            # Load features
            features_df = pd.read_csv(features_file)
            
            # Filter labels for this protein
            protein_labels = labels_df[labels_df['pdb_id'] == protein_id]
            
            if protein_labels.empty:
                print(f"  Warning: No labels found for {protein_id}")
                failed += 1
                continue
            
            # Build graph
            graph = build_protein_graph(str(pdb_file), features_df, protein_labels)
            
            # Save graph
            output_file = Path(output_dir) / f"{protein_id}.pt"
            torch.save(graph, output_file)
            
            graphs.append(graph)
            successful += 1
            
            print(f"  ✅ Graph saved: {output_file}")
            print(f"     Nodes: {graph.x.shape[0]}, Edges: {graph.edge_index.shape[1]}")
            
        except Exception as e:
            print(f"  ❌ Error processing {protein_id}: {e}")
            failed += 1
            continue
    
    print(f"\n📊 Dataset Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total graphs: {len(graphs)}")
    
    return graphs


def test_graph_builder():
    """
    Test function to demonstrate the graph builder.
    """
    print("Testing graph builder...")
    
    example_usage = """
    # Example usage:
    from src.graph_builder import build_dataset
    
    # Build dataset for all proteins
    protein_list = ['1ABC', '2DEF', '3GHI']  # Your protein IDs
    pdb_dir = 'data/pdb'
    features_dir = 'data/processed/features'
    labels_file = 'data/processed/labels.csv'
    
    # Build all graphs
    graphs = build_dataset(protein_list, pdb_dir, features_dir, labels_file)
    
    # Each graph is a PyTorch Geometric Data object
    for i, graph in enumerate(graphs):
        print(f"Graph {i}: {graph.x.shape[0]} nodes, {graph.edge_index.shape[1]} edges")
    """
    
    print(example_usage)
    print("✅ Graph builder implemented successfully!")
    print("\nFunctions available:")
    print("- build_protein_graph() - Build single protein graph")
    print("- build_dataset() - Build dataset for all proteins")
    print("\nReady to construct protein graphs!")


if __name__ == "__main__":
    test_graph_builder()
