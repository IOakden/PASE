import { useState, useEffect } from 'react'
import './App.css'

interface SystemStatus {
  model_status: string
  phase: string
  phase_description: string
  validated_proteins: number
  allosteric_residues: number
}

function App() {
  const [pdbFile, setPdbFile] = useState<File | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  // Fetch system status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status')
        const data = await response.json()
        setSystemStatus(data)
      } catch (error) {
        console.error('Failed to fetch system status:', error)
      }
    }
    
    fetchStatus()
  }, [])

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
    
    try {
      if (searchQuery) {
        // Search for protein
        const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(searchQuery)}`)
        const data = await response.json()
        alert(data.message || 'Search completed')
      } else if (pdbFile) {
        // Upload file
        const formData = new FormData()
        formData.append('file', pdbFile)
        
        const response = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData,
        })
        const data = await response.json()
        alert(data.message || 'File uploaded successfully')
      }
    } catch (error) {
      console.error('API error:', error)
      alert('Error connecting to backend. Make sure the API server is running on port 8000.')
    } finally {
      setIsAnalyzing(false)
    }
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
              <li>Validated proteins: {systemStatus?.validated_proteins ?? 116}</li>
              <li>Allosteric residues identified: {systemStatus?.allosteric_residues?.toLocaleString() ?? '2,137'}</li>
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
                {systemStatus?.model_status ?? 'Loading...'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Phase:</span>
              <span className="status-value">{systemStatus?.phase ?? 'Loading...'}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Dataset:</span>
              <span className="status-value">{systemStatus?.validated_proteins ?? '...'} proteins validated</span>
            </div>
          </div>
          <p className="status-note">
            {systemStatus?.phase_description ?? 'Connecting to backend...'}
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
