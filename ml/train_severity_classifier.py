from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

dataset = load_dataset('json', data_files={'train': 'data/severity_training_data.jsonl', 'val': 'data/severity_val_data.jsonl'})

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)

label_map = {"Routine": 0, "Urgent": 1, "Critical": 2}

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
        "f1": f1_score(labels, predictions, average="weighted")
    }

training_args = TrainingArguments(
    output_dir="./models/severity_classifier",
    learning_rate=3e-5,
    per_device_train_batch_size=64,  
    num_train_epochs=3,
    eval_strategy="epoch",  
    save_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["val"],
    compute_metrics=compute_metrics
)

trainer.train()
trainer.save_model("./models/severity_classifier")
tokenizer.save_pretrained("./models/severity_classifier")