from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
labels = ["negative", "neutral", "positive"]


def analyze_sentiment(headlines: list) -> dict:
    results = {'positive': 0, 'neutral': 0, 'negative': 0}

    inputs = tokenizer(headlines, return_tensors="pt", padding=True, truncation=True)
    outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    preds = torch.argmax(probs, dim=-1)

    for p in preds:
        results[labels[p]] += 1

    return results