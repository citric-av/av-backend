from datasets import load_dataset
from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments

# Load the dataset
dataset = load_dataset("cnn_dailymail", '3.0.0')

# Load the tokenizer
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

# Tokenize the dataset
def preprocess_function(examples):
    inputs = [doc for doc in examples["article"]] 
    model_inputs = tokenizer(inputs, max_length=1024, truncation=True)
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(examples["highlights"], max_length=142, truncation=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_datasets = dataset.map(preprocess_function, batched=True)

# Split the dataset into training and validation sets
train_dataset = tokenized_datasets["train"]
eval_dataset = tokenized_datasets["validation"]

# Load the model
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

# Define the training arguments
training_args = TrainingArguments(
    output_dir='./results',          # output directory for model checkpoints
    num_train_epochs=3,              # number of training epochs
    per_device_train_batch_size=4,   # batch size for training
    per_device_eval_batch_size=4,    # batch size for evaluation
    warmup_steps=500,                # number of warmup steps for learning rate scheduler
    weight_decay=0.01,               # weight decay for optimizer
    logging_dir='./logs',            # directory for storing logs
    save_strategy='epoch',           # save strategy to save the model
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer
)

# Train the model
trainer.train()

