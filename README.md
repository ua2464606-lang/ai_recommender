# NeuralFind - Universal AI Recommendation Engine

Production-ready semantic recommendation app built with Python, FAISS, Flask, SQLite, Bootstrap 5, and TF-IDF.

## Features

- Semantic search: find recommendations by meaning, not only keywords
- Five categories: Movies, Games, Courses, Books, and Software
- FAISS vector index for fast cosine-similarity search
- Category filtering and match scores
- Session-based favorites, recently viewed items, and search history
- Trending searches based on real usage, with curated defaults
- Responsive dark UI built with Bootstrap 5 and custom CSS

## Project Structure

```text
ai_recommender/
|-- app.py
|-- recommendation.index
|-- metadata.pkl
|-- requirements.txt
|-- NeuralFind_AI_Recommendation_Engine.ipynb
|-- datasets/
|   |-- movies.csv
|   |-- games.csv
|   |-- courses.csv
|   |-- books.csv
|   `-- software.csv
|-- database/
|   `-- recommender.db
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- favorites.html
|   `-- history.html
`-- static/
    |-- css/style.css
    `-- js/main.js
```

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5000
```

On Windows, session state is stored by default in `%LOCALAPPDATA%\NeuralFind\recommender.db` to avoid SQLite locking issues inside OneDrive-synced folders. You can override it with:

```bash
set NEURALFIND_DB_PATH=C:\path\to\recommender.db
```

## Example Queries

```text
I want to learn Artificial Intelligence
Open world fantasy RPG games like Skyrim
Sci-fi movies about space and time travel
Cybersecurity hacking tools and books
Learn Python programming from scratch
Best data science courses for beginners
Graphic design and creative software
Productivity and note-taking apps
```

## Stack

| Component | Technology |
| --- | --- |
| Backend | Python 3.10+, Flask 3 |
| Database | SQLite, SQLAlchemy ORM |
| Search | TF-IDF vectors, FAISS IndexFlatIP |
| Frontend | Bootstrap 5, Bootstrap Icons, Vanilla JS |
| Fonts | Syne, Space Grotesk |

## Extending

To add more items, edit the CSV files in `datasets/` and rebuild `recommendation.index` plus `metadata.pkl` from the notebook.

To add a new category, add the CSV, include it in the notebook merge step, rebuild the index, and add the category to `CATEGORY_ICONS` in `app.py` and the category list in `templates/index.html`.
