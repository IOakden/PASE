import { useState } from 'react'
import './App.css'

function App() {
  const [pdbFile, setPdbFile] = useState<File | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setPdbFile(file)
      setSearchQuery('') // Clear search if file is uploaded
    }
  }

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value)
    if (event.target.value) {
      setPdbFile(null) // Clear file if searching
    }
  }

  const handleAnalyze = async () => {
    if (!pdbFile && !searchQuery) return
    
    setIsAnalyzing(true)
    // TODO: Send to backend for analysis
    setTimeout(() => {
      setIsAnalyzing(false)
      alert('Analysis functionality coming soon!')
    }, 1000)
  }

  const canAnalyze = (pdbFile !== null || searchQuery.trim() !== '') && !isAnalyzing

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>PASE</h1>
          <p className="subtitle">Protein Allosteric Site Prediction using Graph Neural Networks</p>
        </div>
      </header>

      <main className="main-content">
        <section className="upload-section">
          <h2>Predict Allosteric Sites</h2>
          <p className="description">
            Search for a protein by PDB ID or UniProt ID, or upload your own structure file.
          </p>

          {/* Search Option */}
          <div className="search-area">
            <label htmlFor="protein-search" className="search-label">
              Search for a protein
            </label>
            <input
              type="text"
              id="protein-search"
              className="search-input"
              placeholder="Enter PDB ID (e.g., 3UO9) or UniProt ID"
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>

          {/* Divider */}
          <div className="divider">
            <span className="divider-text">OR</span>
          </div>

          {/* Upload Option */}
          <div className="upload-area">
            <label htmlFor="pdb-upload" className="upload-label">
              Upload PDB file
            </label>
            <input
              type="file"
              id="pdb-upload"
              accept=".pdb"
              onChange={handleFileUpload}
              className="file-input"
            />
            <label htmlFor="pdb-upload" className="file-label">
              {pdbFile ? (
                <div className="file-selected">
                  <span className="file-indicator">File selected:</span>
                  <span className="file-name">{pdbFile.name}</span>
                </div>
              ) : (
                <div className="file-prompt">
                  <span className="upload-text">Select PDB File</span>
                  <span className="upload-hint">Click to browse or drag and drop</span>
                </div>
              )}
            </label>
          </div>

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={!canAnalyze}
          >
            {isAnalyzing ? 'Analyzing Structure...' : 'Predict Allosteric Sites'}
          </button>
        </section>

        <section className="info-section">
          <div className="info-card">
            <h3>About PASE</h3>
            <p>
              PASE employs a Graph-based Geometric Vector Perceptron (GVP) neural network 
              architecture to predict allosteric binding sites from protein three-dimensional 
              structure. The model analyzes geometric and chemical features of protein residues 
              to identify potential regulatory binding pockets.
            </p>
          </div>

          <div className="info-card">
            <h3>Methodology</h3>
            <ol>
              <li>Search for protein or upload structure in PDB format</li>
              <li>Structure is parsed and converted to geometric graph representation</li>
              <li>GVP-GNN analyzes spatial and chemical features</li>
              <li>Model predicts probability scores for each residue</li>
              <li>Results displayed with interactive visualization</li>
            </ol>
          </div>

          <div className="info-card">
            <h3>Training Dataset</h3>
            <ul>
              <li>Source: ASBench Core Set of validated allosteric proteins</li>
              <li>Validated proteins: 116</li>
              <li>Allosteric residues identified: 2,137</li>
              <li>Training approach: Structure-based binding site definition</li>
              <li>Class balance: 4.46% positive class</li>
            </ul>
          </div>
        </section>

        <section className="status-section">
          <h3>System Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Model:</span>
              <span className="status-value">
                <span className="status-indicator training"></span>
                Training in progress
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Phase:</span>
              <span className="status-value">2 of 12 complete</span>
            </div>
            <div className="status-item">
              <span className="status-label">Dataset:</span>
              <span className="status-value">116 proteins validated</span>
            </div>
          </div>
          <p className="status-note">
            Current stage: Data validation complete. Next: Preprocessing and feature extraction.
          </p>
        </section>
      </main>

      <footer className="footer">
        <p>PASE: Protein Allosteric Site Prediction | Computational Biology Research Tool</p>
        <p className="footer-tech">Built with React, TypeScript, and Geometric Vector Perceptron GNN</p>
      </footer>
    </div>
  )
}

export default App
