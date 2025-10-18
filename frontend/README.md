# PASE Frontend

React + TypeScript frontend for the PASE (Protein Allosteric Site Prediction) application.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **CSS3** - Modern styling with custom properties

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Opens at `http://localhost:5173` (or next available port)

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx           # Main application component
│   ├── App.css           # Application styles
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── vite.config.ts        # Vite configuration
```

## Features

### Current (Scaffold)

- ✅ Modern, responsive UI
- ✅ PDB file upload interface
- ✅ Project information cards
- ✅ Model status indicator
- ✅ Dark theme with gradient accents

### Coming Soon

- [ ] Backend API integration
- [ ] Real-time prediction results
- [ ] 3D protein visualization (NGL Viewer)
- [ ] Interactive residue highlighting
- [ ] Prediction confidence scores
- [ ] Download results functionality
- [ ] Batch processing support

## Backend Integration

When the backend is ready, the frontend will connect to:

```
POST /api/predict
Content-Type: multipart/form-data

Response:
{
  "pdb_id": "protein_name",
  "allosteric_residues": [
    { "chain": "A", "residue": 145, "probability": 0.92 },
    { "chain": "A", "residue": 209, "probability": 0.87 },
    ...
  ],
  "visualization_url": "/api/visualize/protein_name"
}
```

## Styling

The app uses CSS custom properties for theming:

- Primary: Indigo (#6366f1)
- Secondary: Purple (#8b5cf6)
- Background: Slate (#0f172a)
- Dark mode optimized

## Development Notes

- TypeScript strict mode enabled
- ESLint configured for React + TypeScript
- Vite for fast HMR (Hot Module Replacement)
- Mobile-responsive design

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

Part of the PASE project. See main project README for contribution guidelines.
