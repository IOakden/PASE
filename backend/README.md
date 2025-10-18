# PASE Backend API

FastAPI backend for the Protein Allosteric Site Prediction application.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Biopython** - PDB file parsing
- **CORS** - Frontend integration

## Setup

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or use the main project virtual environment:

```bash
cd /Users/izaakoakden/PASE
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Run Development Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Or from project root:

```bash
cd /Users/izaakoakden/PASE
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**

### API Documentation

FastAPI provides automatic interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Root
```
GET /
```
Returns API information and available endpoints.

### System Status
```
GET /api/status
```
Returns current model training status and dataset statistics.

**Response:**
```json
{
  "model_status": "training",
  "phase": "2 of 12 complete",
  "phase_description": "Data validation complete...",
  "validated_proteins": 116,
  "allosteric_residues": 2137
}
```

### Search Protein
```
GET /api/search?query=3UO9
```
Search for a protein by PDB ID or UniProt ID.

**Parameters:**
- `query` (string): PDB ID or UniProt ID

**Response:**
```json
{
  "query": "3UO9",
  "found": false,
  "message": "Protein search functionality will be implemented...",
  "available_datasets": ["ASBench validated proteins"]
}
```

### Upload PDB File
```
POST /api/upload
Content-Type: multipart/form-data
```
Upload a PDB file for analysis.

**Body:**
- `file`: PDB file (multipart/form-data)

**Response:**
```json
{
  "filename": "protein.pdb",
  "size": 12345,
  "status": "received",
  "message": "File uploaded successfully..."
}
```

### Predict Allosteric Sites
```
POST /api/predict
Content-Type: application/json
```
Predict allosteric sites for a protein (available after model training).

**Body:**
```json
{
  "protein_id": "3UO9",
  "source": "pdb"
}
```

**Response (when model is trained):**
```json
{
  "protein_id": "3UO9",
  "total_residues": 320,
  "predicted_allosteric": 25,
  "residues": [
    {
      "chain": "A",
      "residue_number": 145,
      "residue_name": "LEU",
      "probability": 0.92,
      "allosteric": true
    }
  ],
  "visualization_url": "/api/visualize/3UO9"
}
```

### Health Check
```
GET /api/health
```
Simple health check endpoint.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py       # Package init
│   ├── main.py           # FastAPI application
│   ├── models.py         # Pydantic models (future)
│   ├── routes/           # API routes (future)
│   │   ├── predict.py
│   │   ├── upload.py
│   │   └── search.py
│   └── services/         # Business logic (future)
│       ├── pdb_parser.py
│       ├── model_inference.py
│       └── database.py
├── tests/                # API tests
├── requirements.txt      # Dependencies
└── README.md
```

## CORS Configuration

The API allows requests from:
- http://localhost:5173 (Vite default)
- http://localhost:5174 (Vite alternate)
- http://localhost:3000 (React default)

Additional origins can be added in `app/main.py`.

## Development Workflow

### Current Status (Phase 2 Complete)

The API currently returns **placeholder responses** because:
- Model training hasn't started yet (Phase 7)
- Preprocessing pipeline needs to be built (Phase 3-4)

### Endpoints Ready for Integration

1. ✅ `/api/status` - Works now, returns real data
2. ⏳ `/api/search` - Returns placeholder, needs protein database
3. ⏳ `/api/upload` - Accepts files, needs processing pipeline
4. ⏳ `/api/predict` - Returns 503, needs trained model

### Next Steps

1. **Phase 3-6**: Build preprocessing and training pipeline
2. **Integrate model**: Connect trained GVP-GNN to `/api/predict`
3. **Add PDB parsing**: Use Biopython to process uploaded files
4. **Database**: Add protein metadata database for search
5. **Visualization**: Generate 3D structure visualizations

## Testing

### Manual Testing

Use curl or httpie:

```bash
# Get status
curl http://localhost:8000/api/status

# Search protein
curl "http://localhost:8000/api/search?query=3UO9"

# Upload file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@protein.pdb"

# Health check
curl http://localhost:8000/api/health
```

### Interactive Testing

Visit http://localhost:8000/docs for Swagger UI with interactive API testing.

## Integration with Frontend

Update frontend to call API:

```typescript
// Example API call from React
const response = await fetch('http://localhost:8000/api/status');
const status = await response.json();
```

The frontend at http://localhost:5174 is already configured to send requests to this backend.

## Environment Variables

Create `.env` file (optional):

```bash
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

## Production Deployment

For production, use:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with Gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Notes

- API follows RESTful conventions
- All responses are JSON
- Error messages are descriptive
- CORS is enabled for local development
- Automatic API documentation via FastAPI

