import pytest

from ragcore.llms import BaseLLM, EchoLLM
from ragcore.models import Chunk, SearchResult
from ragcore.prompts import build_prompt


def _results():
    c = Chunk(id="attn:p5:c17", doc_id="attn", text="h = 8 parallel attention heads", page=5)
    return [SearchResult(chunk=c, score=0.55)]


def test_prompt_contains_context_and_question():
    p = build_prompt("How many heads?", _results())
    assert "h = 8 parallel attention heads" in p
    assert "How many heads?" in p


def test_prompt_carries_citation_metadata():
    p = build_prompt("How many heads?", _results())
    assert "page 5" in p
    assert "attn" in p          # multi-paper: which document


def test_prompt_states_grounding_rules():
    p = build_prompt("q", _results())
    assert "ONLY" in p
    assert "Not found in the provided papers." in p


def test_echo_llm_records_prompt():
    llm = EchoLLM(canned="hello")
    assert llm.generate("my prompt") == "hello"
    assert llm.last_prompt == "my prompt"


def test_echo_fulfills_contract():
    assert isinstance(EchoLLM(), BaseLLM)