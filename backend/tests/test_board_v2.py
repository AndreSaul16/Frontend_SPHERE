"""Tests del Board Meeting V2: parser de votos, tally/consenso, routing fan-out,
reducer de votos y partial_refund del triage."""
import pytest

from app.application.board_v2 import (
    _parse_vote,
    _strip_vote_line,
    _tally,
    route_after_triage,
    route_analysis,
    route_after_consensus,
    route_after_rebuttal,
    BOARD_DIRECTORS,
)
from app.application.orchestrator import _merge_board_votes


# --- Parser de votos ---

def test_parse_vote_basico():
    assert _parse_vote("análisis...\n[VOTO] decision=SI confianza=85") == {"decision": "SI", "confidence": 85}


def test_parse_vote_condicional_minuscula():
    # case-insensitive en la etiqueta
    assert _parse_vote("[voto] decision=condicional confianza=40") == {"decision": "CONDICIONAL", "confidence": 40}


def test_parse_vote_clamp_confianza():
    assert _parse_vote("[VOTO] decision=NO confianza=150")["confidence"] == 100


def test_parse_vote_sin_linea():
    assert _parse_vote("texto sin voto") is None


def test_parse_vote_none_seguro():
    assert _parse_vote("") is None


def test_strip_vote_line_quita_voto():
    txt = "Mi análisis es sólido.\n\n[VOTO] decision=SI confianza=90"
    assert _strip_vote_line(txt) == "Mi análisis es sólido."


# --- Tally / consenso ---

def test_tally_unanime():
    votes = {"CTO": {"decision": "SI", "confidence": 80}, "CFO": {"decision": "SI", "confidence": 90}}
    t = _tally(votes)
    assert t["unanimous"] is True and t["winner"] == "SI" and t["avg_confidence"] == 85


def test_tally_dividido_no_unanime():
    votes = {"CTO": {"decision": "SI", "confidence": 80}, "CFO": {"decision": "NO", "confidence": 60}}
    t = _tally(votes)
    assert t["unanimous"] is False and t["total"] == 2


def test_tally_ignora_sentinel():
    votes = {"__RESET__": True, "CTO": {"decision": "NO", "confidence": 70}}
    t = _tally(votes)
    assert t["total"] == 1 and t["counts"]["NO"] == 1


# --- Reducer de votos (acumulación paralela + reset) ---

def test_merge_votes_acumula():
    left = {"CTO": {"decision": "SI", "confidence": 80}}
    right = {"CFO": {"decision": "NO", "confidence": 60}}
    merged = _merge_board_votes(left, right)
    assert set(merged.keys()) == {"CTO", "CFO"}


def test_merge_votes_reset():
    left = {"CTO": {"decision": "SI", "confidence": 80}}
    assert _merge_board_votes(left, {"__RESET__": True}) == {}


# --- Routing ---

def test_route_after_triage_regenera_va_a_synthesis():
    assert route_after_triage({"board_regenerate": True}) == "synthesis"


def test_route_after_triage_normal_va_a_ceo():
    assert route_after_triage({"board_regenerate": False}) == "ceo_open"


def test_route_analysis_fanout_por_participantes():
    nodes = route_analysis({"board_participants": ["CTO", "CFO"]})
    assert sorted(nodes) == ["cfo_analysis", "cto_analysis"]


def test_route_analysis_default_full_board():
    nodes = route_analysis({})
    assert sorted(nodes) == sorted(f"{r.lower()}_analysis" for r in BOARD_DIRECTORS)


def test_route_after_consensus_early_exit_sin_devil():
    # unánime con confianza alta → salta réplicas, va a síntesis (sin devil)
    state = {
        "board_votes": {"CTO": {"decision": "SI", "confidence": 80}, "CFO": {"decision": "SI", "confidence": 90}},
        "board_participants": ["CTO", "CFO"],
        "board_devil": False,
    }
    assert route_after_consensus(state) == ["synthesis"]


def test_route_after_consensus_early_exit_con_devil():
    state = {
        "board_votes": {"CTO": {"decision": "SI", "confidence": 80}, "CFO": {"decision": "SI", "confidence": 90}},
        "board_participants": ["CTO", "CFO"],
        "board_devil": True,
    }
    assert route_after_consensus(state) == ["devil"]


def test_route_after_consensus_sin_consenso_va_a_replicas():
    state = {
        "board_votes": {"CTO": {"decision": "SI", "confidence": 80}, "CFO": {"decision": "NO", "confidence": 60}},
        "board_participants": ["CTO", "CFO"],
        "board_devil": False,
    }
    assert sorted(route_after_consensus(state)) == ["cfo_rebuttal", "cto_rebuttal"]


def test_route_after_rebuttal_devil_flag():
    assert route_after_rebuttal({"board_devil": True}) == "devil"
    assert route_after_rebuttal({"board_devil": False}) == "synthesis"


def test_board_v2_graph_compila():
    from app.application.board_v2 import board_workflow_v2
    # Compila sin checkpointer (valida estructura de nodos/edges/fan-out).
    assert board_workflow_v2.compile() is not None


# --- partial_refund del CreditManager ---

def test_partial_refund_clamp_y_transaccion():
    from app.application.credit_manager import CreditManager, ChargeContext

    class FakeCol:
        def __init__(self):
            self.updates = []
            self.inserts = []
        def update_one(self, *a, **k):
            self.updates.append((a, k))
        def insert_one(self, doc):
            self.inserts.append(doc)

    cm = CreditManager.__new__(CreditManager)
    cm.users_collection = FakeCol()
    cm.transactions_collection = FakeCol()

    ctx = ChargeContext(tx_id="tx_x", user_id="u1", cost=5, source="plan", counted_as=5)
    cm.partial_refund(ctx, 2)
    # Devuelve 2 al bucket plan + registra transacción +2
    assert cm.users_collection.updates, "debe hacer $inc"
    assert cm.transactions_collection.inserts[0]["delta"] == 2
    assert cm.transactions_collection.inserts[0]["reason"] == "board_triage_reduced"


def test_partial_refund_clamp_no_devuelve_de_mas():
    from app.application.credit_manager import CreditManager, ChargeContext

    class FakeCol:
        def __init__(self):
            self.inserts = []
        def update_one(self, *a, **k):
            pass
        def insert_one(self, doc):
            self.inserts.append(doc)

    cm = CreditManager.__new__(CreditManager)
    cm.users_collection = FakeCol()
    cm.transactions_collection = FakeCol()
    ctx = ChargeContext(tx_id="tx_x", user_id="u1", cost=5, source="topup", counted_as=5)
    cm.partial_refund(ctx, 99)  # se clampa a 5
    assert cm.transactions_collection.inserts[0]["delta"] == 5
