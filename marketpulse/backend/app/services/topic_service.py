from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation


def extract_lda_topics(
    texts: list[str],
    n_topics: int = 5,
    n_words: int = 8,
    num_topics: int | None = None,
) -> list[dict]:
    """Extract LDA topics from real text only. Returns [] when text is insufficient or modeling fails."""
    if num_topics is not None:
        n_topics = num_topics

    clean_texts = [str(t).strip() for t in texts if t and len(str(t).strip()) > 8]
    if len(clean_texts) < 2:
        return []

    try:
        vectorizer = CountVectorizer(
            stop_words="english",
            max_df=0.95,
            min_df=1,
            max_features=1000,
        )
        matrix = vectorizer.fit_transform(clean_texts)
        if matrix.shape[1] == 0:
            return []

        lda = LatentDirichletAllocation(
            n_components=max(1, min(n_topics, len(clean_texts))),
            random_state=42,
            learning_method="batch",
        )
        lda.fit(matrix)
        words = vectorizer.get_feature_names_out()

        topics = []
        for idx, topic in enumerate(lda.components_):
            top_words = [words[i] for i in topic.argsort()[-n_words:][::-1]]
            topics.append({
                "topic_id": idx + 1,
                "keywords": top_words,
                "label": ", ".join(top_words[:4]),
            })
        return topics
    except Exception:
        return []
