# MatchLens Frontend

The React frontend application for MatchLens, providing an AI-assisted reciprocal matchmaking interface.

## Technology Stack
- **React** (v19) with **Vite**
- **Tailwind CSS** (v4)
- **React Router** (v7)
- **Lucide React** (Icons)
- **Framer Motion** (Subtle UI animations)

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL` points to your running MatchLens FastAPI backend (default: `http://localhost:8000`).

### 3. Run Development Server
```bash
npm run dev
```
The application will be accessible at `http://localhost:3000`.

### 4. Build for Production
```bash
npm run build
```
