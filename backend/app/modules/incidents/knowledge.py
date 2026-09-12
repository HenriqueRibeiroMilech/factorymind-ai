import hashlib
import re
from pathlib import Path

from flask import current_app
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOP_WORDS = "a o as os de da do das dos e em um uma uns umas para por com que no na nos nas ao aos se ou como foi esta este esse essa pelo pela mais durante".split()


def retrieve(category, query, limit=4):
    """Small area-specific corpus, split by Markdown sections; no unrelated fallback."""
    directory = Path(current_app.config["KNOWLEDGE_DIR"]) / category
    chunks = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].removeprefix("# ")
        for heading, body in re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S):
            excerpt = body.strip()
            chunks.append({"id": f"{category}/{path.stem}:{hashlib.sha256(excerpt.encode()).hexdigest()[:8]}",
                           "document": f"{category}/{path.name}", "title": title,
                           "section": heading.strip(), "excerpt": excerpt, "fictional": True})
    if not chunks or not query.strip():
        return []
    vectorizer = TfidfVectorizer(strip_accents="unicode", lowercase=True, stop_words=STOP_WORDS, ngram_range=(1, 2))
    documents = [chunk["section"] + " " + chunk["excerpt"] for chunk in chunks]
    matrix = vectorizer.fit_transform(documents)
    word_scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
    # Character n-grams bridge ordinary inflections such as "vibrou" / "vibração".
    # Remove stop words before this pass so common fragments do not dominate.
    tokenize = TfidfVectorizer(strip_accents="unicode", stop_words=STOP_WORDS).build_analyzer()
    normalized = [" ".join(tokenize(text)) for text in documents]
    characters = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    character_matrix = characters.fit_transform(normalized)
    character_scores = cosine_similarity(characters.transform([" ".join(tokenize(query))]), character_matrix)[0]
    scores = 0.6 * word_scores + 0.4 * character_scores
    order = sorted(range(len(chunks)), key=lambda index: (-scores[index], chunks[index]["id"]))
    return [{**chunks[index], "similarity": round(float(scores[index]), 4)}
            for index in order[:limit] if scores[index] >= 0.07]
