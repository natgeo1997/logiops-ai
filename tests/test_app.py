from types import SimpleNamespace
from unittest.mock import MagicMock
from pathlib import Path
import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest
import app

@pytest.mark.parametrize('priority', ['Critical','High','Medium','Low'])
def test_supported_priority_and_json_round_trip(priority):
    value = app.Avaliacao(**{**app.DEMO.model_dump(), 'priority': priority})
    assert app.Avaliacao.model_validate_json(value.model_dump_json()) == value

@pytest.mark.parametrize('update', [{'priority': 'Urgent'}, {'operational_impact': ''}, {'recommended_actions': []}, {'preventive_actions': []}])
def test_invalid_assessments_are_rejected(update):
    with pytest.raises(ValidationError):
        app.Avaliacao(**{**app.DEMO.model_dump(), **update})

def test_gemini_request_uses_schema_and_validates_response(monkeypatch):
    factory = MagicMock()
    api = factory.return_value.__enter__.return_value
    api.models.generate_content.return_value = SimpleNamespace(text=app.DEMO.model_dump_json())
    monkeypatch.setattr(app.genai, 'Client', factory)
    assert app.analisar('Fictional report', 'test-key-not-real', 'test-model') == app.DEMO
    request = api.models.generate_content.call_args.kwargs
    assert request['contents'] == 'Fictional report'
    assert request['config'].response_schema is app.Avaliacao
    assert request['config'].response_mime_type == 'application/json'

@pytest.mark.parametrize('text', ['', '{broken', '{}'])
def test_bad_gemini_output_is_rejected(monkeypatch, text):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.models.generate_content.return_value = SimpleNamespace(text=text)
    monkeypatch.setattr(app.genai, 'Client', factory)
    with pytest.raises((ValueError, ValidationError)):
        app.analisar('Fictional report', 'test-key-not-real', 'test-model')

def test_generated_text_is_escaped_in_report():
    value = app.DEMO.model_copy(update={'suggested_communication': '<script>alert(1)</script>'})
    html = app.ficha(value, '<unsafe>', 'test')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html and '&lt;unsafe&gt;' in html

@pytest.mark.parametrize('error,code', [(TimeoutError('private diagnostic'),'TEMPO_ESGOTADO'), (ValueError('private diagnostic'),'RESPOSTA_INVALIDA'), (RuntimeError('private diagnostic'),'CONEXAO')])
def test_error_messages_do_not_expose_raw_diagnostics(error, code):
    result = app.mensagem_erro(error)
    assert result[2] == code
    assert 'private diagnostic' not in ' '.join(result)

def test_demo_ui_works_without_api_call(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    def reject_call(*args, **kwargs):
        raise AssertionError('Demo must not call Gemini')
    monkeypatch.setattr(app.genai, 'Client', reject_call)
    ui = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py').run()
    ui.radio[0].set_value('Ver um exemplo').run()
    ui.button[0].click().run()
    assert not ui.exception
    assert ui.session_state['resultado']['dados']['priority'] == 'High'
    assert ui.session_state['resultado']['modo'] == 'Ver um exemplo'
