# LogiOps AI

**AI-assisted logistics incident analysis** · Python · Streamlit · Gemini

Protótipo independente que transforma relatos de ocorrências logísticas em avaliações estruturadas e sugestões de ações, mantendo a validação com o profissional responsável.

## Funcionalidades

- Interface Streamlit para registrar e analisar ocorrências
- **Demo scenario**: demonstração com cenário fictício, sem consumir API
- **Live analysis**: análise com Gemini via `google-genai`
- Avaliação de prioridade (`Critical`, `High`, `Medium` ou `Low`)
- Impacto operacional, possíveis causas, ações recomendadas e preventivas
- Sugestão de comunicação para revisão humana
- Resposta JSON validada com Pydantic
- Exportação dos resultados em JSON e TXT
- Tratamento de erros de API

## Executar localmente

Requisitos: Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m streamlit run app.py
```

Abra [http://localhost:8501](http://localhost:8501).

Para testar sem chave, selecione **Demo scenario** e clique em **Analyze Incident**. Para a análise real, configure `GEMINI_API_KEY` em `.env` ou nos segredos da hospedagem, reinicie a aplicação e selecione **Live analysis**. Nunca envie `.env` ao repositório.

## Arquitetura

```text
Relato da ocorrência
       ↓
Streamlit / Python
       ↓
Gemini (saída estruturada JSON)
       ↓
Validação com Pydantic
       ↓
Cards de análise e exportação JSON/TXT
       ↓
Revisão humana
```

## Limitações

Protótipo demonstrativo; não há autenticação, banco de dados, envio automático de mensagens ou execução automática de ações. Hipóteses e recomendações da IA exigem revisão humana. Utilize somente dados fictícios ou autorizados.

**Tecnologias:** Python, Streamlit, Gemini API (`google-genai`), Pydantic e CSS.
