from typing import List

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from gliner import GLiNER
import time
import uvicorn
import os
import logging

logging.basicConfig(level=logging.INFO)

logging.info("Starting the server...")

model = GLiNER.from_pretrained(
    os.environ["MODEL_PATH"]
)

# Gliner excels at zero-shot so see the all-training-labels.txt as examples, and you can add similar names to the list (doesn't have to be exactly in the training set)
DEFAULT_LABELS = (
    """person, organization, phone number, address, license key, passport number, email, credit card number, social security number, date of birth, bank account number, medication, driver's license number, tax identification number, medical condition, identity card number, national id number, ip address, email address, iban, credit card expiration date, username, health insurance number, registration number, student id number, insurance number, flight number, landline phone number, blood type, cvv, reservation number, digital signature, social media handle, license plate number, cnpj, postal code, passport_number, serial number, vehicle registration number, credit card brand, fax number, visa number, insurance company, identity document number, transaction number, cvc, ticket number"""
    .split(", "))

logging.info(f"Default labels ({len(DEFAULT_LABELS)}): {DEFAULT_LABELS}")

app = FastAPI()

DEFAULT_THRESHOLD = 0.5


class RedactionRequest(BaseModel):
    text: str
    # default to all
    labels: List[str] = Field(default_factory=lambda: DEFAULT_LABELS)
    redactionFormat: str = "<REDACTED {label}>"
    # default threshold + per label thresholds
    thresholds: dict = Field(default_factory=lambda: {'default': DEFAULT_THRESHOLD})


@app.post("/redact")
async def redact_pii(request: RedactionRequest):
    st = time.time()
    text = request.text
    labels = request.labels or DEFAULT_LABELS
    logging.info(f"Redacting {len(labels)} labels")

    # Use a sliding window because the models are limited
    MAX_CHUNK_LEN = 1000
    CHUNK_OVERLAP = 100
    stride = MAX_CHUNK_LEN - CHUNK_OVERLAP

    chunks = []
    for idx in range(0, len(text), stride):
        end_idx = min(idx + MAX_CHUNK_LEN, len(text))
        chunk_text = text[idx:end_idx]
        chunks.append((chunk_text, idx))

    entities_info = []

    for chunk_text, chunk_start in chunks:
        default_threshold = request.thresholds.get('default', DEFAULT_THRESHOLD)
        min_threshold = min(request.thresholds.values(), default=default_threshold)
        chunk_entities = model.predict_entities(chunk_text, labels, threshold=min_threshold)
        for entity in chunk_entities:
            logging.debug(f"{entity=}")
            entity_text = entity['text']
            entity_label = entity['label']
            entity_start = entity['start']  # offset in chunk_text
            entity_end = entity['end']
            # entity positions in original text:
            global_start = chunk_start + entity_start
            global_end = chunk_start + entity_end

            # per label threshold or default
            if entity['score'] < request.thresholds.get(entity_label, default_threshold):
                logging.debug(f"Skipping {entity_label} with score {entity['score']}")
                continue

            # Avoid duplicates due to overlapping chunks
            if any(e['start'] == global_start and e['end'] == global_end for e in entities_info):
                logging.debug(f"Skipping duplicate {entity_text}")
                continue

            entities_info.append({
                'text': entity_text,
                'label': entity_label,
                'start': global_start,
                'end': global_end,
                'score': entity['score']
            })

    # sort by their position in the text
    entities_info.sort(key=lambda x: x['start'])

    redacted_text = text
    for entity in reversed(entities_info):
        start = entity['start']
        end = entity['end']
        entity_label = entity['label']
        redacted_entity = request.redactionFormat.format(label=entity_label.upper())
        # replace the entity in the redacted text
        redacted_text = redacted_text[:start] + redacted_entity + redacted_text[end:]

    logging.info(f"Redacted in {1000 * (time.time() - st):.2f} ms.")
    return {
        'redactedText': redacted_text,
        'entities': entities_info,
        'labels': labels
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse('index.html')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
