from datasets import load_dataset
from transformers import BartForConditionalGeneration, BartTokenizer, Trainer, TrainingArguments

# Load the dataset
dataset = load_dataset('cnn_dailymail', '3.0.0')

# Prepare the data
tokenizer = BartTokenizer.from_pretrained('facebook/bart-base')

def tokenize_function(examples):
    inputs = tokenizer(examples['article'], truncation=True, max_length=512, padding='max_length', return_tensors='pt')
    outputs = tokenizer(examples['highlights'], truncation=True, max_length=150, padding='max_length', return_tensors='pt')
    inputs["labels"] = outputs["input_ids"]
    return inputs

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Fine-tune the model
model = BartForConditionalGeneration.from_pretrained('facebook/bart-base')

training_args = TrainingArguments(
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    output_dir='./results',
    num_train_epochs=3,
    evaluation_strategy='epoch',
    logging_dir='./logs',
    logging_steps=100,
    do_train=True,
    do_eval=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
)

trainer.train()

# Save the fine-tuned model
model.save_pretrained('./fine_tuned_model')
tokenizer.save_pretrained('./fine_tuned_model')
