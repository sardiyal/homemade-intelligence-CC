"""SQLAlchemy ORM models for all 5 database tables."""

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from backend.database.connection import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    feed_url = Column(Text)
    source_type = Column(Text)  # rss / gdelt / manual / api
    layer = Column(Integer)  # Intelligence stack layer 1-10
    bias_label = Column(Text)  # center / left / right / state-affiliated / independent
    language = Column(Text)  # ISO 639-1
    is_active = Column(Boolean, default=True)
    # Economic school of thought (theoretical framework): neoclassical / keynesian / monetarist /
    # supply-side / austrian / institutional / heterodox / empirical / mixed — null for non-economics sources
    economic_school = Column(Text)
    # Economic policy bias (policy direction, independent of social/political bias):
    # progressive / center / market-oriented / state-directed
    # progressive = favors government intervention, redistribution, regulation
    # market-oriented = favors free markets, deregulation, low taxes
    # state-directed = state-capitalist systems (China, Russia, Gulf states) — different axis entirely
    economic_bias = Column(Text)
    # Analytical/IR theory framework used for geopolitical and social analysis:
    # realist        = power, national interest, security dilemmas, balance of power (Waltz, Mearsheimer)
    # liberal        = institutions, norms, interdependence, democratic peace (Keohane, Ikenberry)
    # constructivist = ideas, identities, norms, social construction of threats (Wendt, Finnemore)
    # critical       = power structures, post-colonialism, hegemony critique (Cox, Gramsci)
    # empirical      = data-driven; no dominant IR theory framework
    # mixed          = deliberately pluralist; applies multiple IR frameworks
    # (omit for sources without a systematic IR/geopolitical analytical stance)
    analytical_framework = Column(Text)
    # Comma-separated domain tags where this source is most salient, e.g. "markets,energy"
    salience_domains = Column(Text)

    ingested_content = relationship("IngestedContent", back_populates="source")


class IngestedContent(Base):
    __tablename__ = "ingested_content"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    content_hash = Column(Text, unique=True, nullable=False, index=True)
    url = Column(Text)
    title = Column(Text)
    body = Column(Text)
    published_at = Column(DateTime)
    ingested_at = Column(DateTime, default=func.now())
    is_manual = Column(Boolean, default=False)
    chroma_doc_id = Column(Text)

    source = relationship("Source", back_populates="ingested_content")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text, nullable=False)
    domain = Column(Text)  # geopolitics / markets / taiwan / energy / general
    status = Column(Text, default="pending")  # pending / generating / complete / failed
    bias_score = Column(Float)  # 0.0-1.0 narrative divergence
    confidence_overall = Column(Text)  # high / medium / low
    content_en = Column(Text)
    content_zh_tw = Column(Text)
    content_zh_tw_elder = Column(Text)
    source_ids_json = Column(Text)  # JSON array of ingested_content IDs
    tokens_used = Column(Integer, default=0)
    tokens_cached = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    chroma_doc_id = Column(Text)

    predictions = relationship("Prediction", back_populates="report")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text, nullable=False)
    prediction_text = Column(Text, nullable=False)
    confidence_pct = Column(Integer)  # 1-99
    domain = Column(Text)  # geopolitics / markets / taiwan / energy / other
    deadline_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    outcome = Column(Text)  # NULL / correct / incorrect / partial
    resolution_notes = Column(Text)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    metaculus_question_id = Column(Text)
    polymarket_market_id = Column(Text)
    metaculus_community_pct = Column(Float)
    polymarket_odds_pct = Column(Float)

    report = relationship("Report", back_populates="predictions")
    outcomes = relationship("PredictionOutcome", back_populates="prediction")


class PredictionOutcome(Base):
    __tablename__ = "prediction_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    scored_at = Column(DateTime, default=func.now())
    forecast = Column(Float, nullable=False)  # confidence_pct / 100
    outcome_binary = Column(Float, nullable=False)  # 1.0 / 0.0 / 0.5
    brier_score = Column(Float, nullable=False)  # (forecast - outcome_binary)^2

    prediction = relationship("Prediction", back_populates="outcomes")
