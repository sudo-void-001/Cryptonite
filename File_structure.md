Cryptonite/
├── docs/
│   ├── PRD.md                 ← product requirements
│   ├── ARCHITECTURE.md        ← system design, data flow, decisions
│   ├── PHASES.md              ← implementation plan with acceptance criteria
│   ├── DESIGN.md              ← UI/visual reference
│   └── ALGORITHMS.md          ← math specs for each carrier
├── core/                      ← empty folders with __init__.py stubs
│   ├── __init__.py
│   ├── crypto.py              ← stub with docstrings only
│   ├── prng.py
│   ├── payload.py
│   └── carriers/
│       ├── __init__.py
│       ├── png.py
│       ├── jpeg.py
│       └── mp3.py
├── tests/                     ← empty but structured
│   ├── test_crypto.py
│   ├── test_png.py
│   ├── test_jpeg.py
│   └── test_mp3.py
├── requirements.txt           ← pinned dependencies
├── pyproject.toml             ← project metadata
└── .env.example               ← env vars template