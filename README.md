# pii-redaction-service

**🚪 Live Demo: [pii-redaction.toppe.dev](https://pii-redaction.toppe.dev)**

🚀 **pii-redaction-service** is your go-to service for removing Personally Identifiable Information (PII) from text. Whether you're prepping data for a
third-party
service or storing it in your database, this tool has you covered. 🌟

This bad boy is powered by the multilingual **GLiNER** model: [GLiNER on Hugging Face](https://huggingface.co/urchade/gliner_multi_pii-v1) 🤗. So, whether it’s
English, or Spanish, we’re here to keep your data safe (or at least attempt to). 🛡️

---

## 🤔 Why Do You Need This?

- ✂️ **Trim Your Data**: Remove PII before sending text to third-party services like ChatGiPpiTy.
- 🛡️ **Privacy Protector**: Ensure your database isn’t a liability waiting to happen.
- 🤖 **Model-Ready Data**: Pre-cleaned, privacy-safe data for your ML pipelines.

> **Caution**: This isn't magic pixie dust, folks. While GLiNER is a rockstar, no model is perfect.

---

## 💾 Minimum Requirements

- 🧠 2GB RAM
- ⚙️ 1 CPU core (you can run this on a potato 🥔)
- 📦 Image size: <3GB (slim and trim like your favorite OF model)

---

## 🛠️ How To Get Started

Running this is easier than microwaving popcorn 🍿. Just:

1. Install Docker (duh). 🐳
2. Run this single line in your terminal (or command prompt, if you're feeling fancy):

```bash
bash run.sh

```

That’s it! The service will be up and slicing PII at `http://localhost:8000`. 🎉

---

## 🔥 Why This is the Coolest Thing You’ll Use Today

- 🛡️ **Multilingual**: Handles PII in multiple languages.
- 🏃 **Fast and Lightweight**: Doesn’t hog your system resources.
- 🎉 **Open Source Glory**: Fork it. Star it. Brag about it.
- 🤯 **Dockerized**: One command and you’re golden.

---

## 🤩 Star This Repo or I’ll Cry 😢

---

## ⚠️ Legalese and Disclaimer

This is a tool. It’s awesome, but it’s not a lawyer. Don’t trust it to solve all your problems, and don’t blame me if you don't know what you're doing.
Stay smart, stay safe. 🙃

---

## 📬 API Usage

This will start the service on `http://localhost:8000` (demo UI).

Call the API with a POST request to `http://localhost:8000/redact` with the following JSON payload:

```json
{
  "text": "To help, I'll give my credit card number that is 4242 4242 4242 4242 and the CVV 3 digits on the back are 362"
}
```

For example:

```bash
curl -X POST "http://localhost:8000/redact" -H "accept: application/json" -H "Content-Type: application/json" -d "{\"text\":\"To help, I'll give my credit card number that is 4242 4242 4242 4242 and the CVV 3 digits on the back are 362\"}"
```

Output:

```json
{
  "redactedText": "To help, I'll give my credit card number that is <REDACTED CREDIT CARD NUMBER> and the CVV 3 digits on the back are <REDACTED CVV>",
}
```
(includes more fields, see below)  
Data cleaned faster than you can say “GDPR-compliant.”* 🔥

--- 

GLiNER masters zero-shot entity recognition so you can include any custom PII label in the request and some other parameters too:

See `training-labels.txt` file for inspiration for labels - it doesn't have to be exactly like in the training data.

```json
{
  "text": "Toppe's super private text with license key 1234-5678-9012-3456",
  "labels": [
    "user id",
    "username",
    "license key"
  ],
  "thresholds": {
    "default": 0.5,
    "license key": 0.4,
    "username": 1
  },
  "redactionFormat": "[REDACTED]"
}
```

`threshold` (default 0.5) is a value between 0 and 1. The higher the value, the more confident the model has to be to redact the text.
You can set a `default` threshold for all labels and a specific threshold for a specific label. Set threshold to 1 to prevent redaction of a label.

For example:

```bash
curl -X POST "http://localhost:8000/redact" -H "accept: application/json" -H "Content-Type: application/json" -d "{\"text\":\"Toppe's super private text with license key 1234-5678-9012-3456\",\"labels\":[\"user id\",\"username\",\"license key\"],\"thresholds\":{\"default\":0.5,\"license key\":0.4,\"username\":1},\"redactionFormat\":\"[REDACTED]\"}"
```

Output:

```json
{
  "redactedText": "Toppe's super private text with license key [REDACTED]",
  "entities": [
    {
      "text": "1234-5678-9012-3456",
      "label": "license key",
      "start": 41,
      "end": 60,
      "score": 0.9226852059364319
    }
  ],
  "labels": [
    "user id",
    "username",
    "license key"
  ]
}
```

Note: `threshold` (default 0.5) is a value between 0 and 1. The higher the value, the more confident the model has to be to redact the text.
`redactionFormat` (default `<REDACTED {label}>`) is the format of the redacted text. `{label}` will be replaced with the uppercase label.

## Known Issues

- The model is not perfect and may not redact all PII. Use responsibly.
- The model removes text similar to the label that is not PII. E.g., text "phone numbers" may be redacted if label "phone number" is enabled even though there's
  no phone number.
- In long texts, the service chunks (a sliding window) the text which may cut entities in half and incorrectly redact it only partially PII
- Sometimes a part of longer entity will be redacted as something else. E.g., "123 Avenida Central, Madrid, Spain, 28014" may be redacted as "[REDACTED CCV] Avenida Central, Madrid, Spain, 28014"