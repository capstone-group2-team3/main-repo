import numpy as np
import os
import json
from pathlib import Path
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

os.environ.setdefault("HF_HOME", ".cache/huggingface")
os.environ.setdefault("HF_DATASETS_CACHE", ".cache/huggingface/datasets")

dataset = load_dataset(
    "json",
    data_files={
        "train": "data/severity_training_data.jsonl",
        "val": "data/severity_val_data.jsonl",
    },
    cache_dir=".cache/huggingface/datasets",
)

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

label_map = {"Routine": 0, "Urgent": 1, "Critical": 2}
id2label = {index: label for label, index in label_map.items()}
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=3,
    id2label=id2label,
    label2id=label_map,
)


def tokenize_function(examples):
    tokenized = tokenizer(examples["text"], padding="max_length", max_length=64, truncation=True)
    tokenized["labels"] = [label_map[label] for label in examples["label"]]
    return tokenized


tokenized_datasets = dataset.map(tokenize_function, batched=True, remove_columns=["text", "label"])


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1": f1_score(labels, predictions, average="weighted"),
    }


training_args = TrainingArguments(
    output_dir="./models/severity_classifier",
    learning_rate=3e-5,
    per_device_train_batch_size=64,
    per_device_eval_batch_size=64,
    num_train_epochs=3,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_strategy="epoch",
    seed=42,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["val"],
    compute_metrics=compute_metrics
)

train_result = trainer.train()
trainer.save_metrics("train", train_result.metrics)
eval_metrics = trainer.evaluate()
trainer.save_metrics("eval", eval_metrics)
trainer.save_model("./models/severity_classifier")
tokenizer.save_pretrained("./models/severity_classifier")

special_tokens_path = Path("models/severity_classifier/special_tokens_map.json")
if not special_tokens_path.exists():
    special_tokens_path.write_text(
        json.dumps(tokenizer.special_tokens_map, indent=2, sort_keys=True),
        encoding="utf-8",
    )
