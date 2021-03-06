from datasets import load_dataset, load_metric
import random
import pandas as pd
import numpy as np
from transformers import Wav2Vec2ForCTC,Wav2Vec2CTCTokenizer, TrainingArguments\
    , Trainer, Wav2Vec2Processor, Wav2Vec2FeatureExtractor
import re
import json
import soundfile as sf
from data_collector import DataCollatorCTCWithPadding
import sys

PREPATH = ""

if len(sys.argv) > 1:
    PREPATH = sys.argv[1]

librispeech = load_dataset("librispeech_asr", cache_dir=PREPATH + '/dataset')
librispeech = librispeech.remove_columns(["phonetic_detail", "word_detail", "dialect_region", "id", "sentence_type", "speaker_id"])


def show_random_elements(dataset, num_examples=10):
    assert num_examples <= len(dataset), "Can't pick more elements than there are in the dataset."
    picks = []
    for _ in range(num_examples):
        pick = random.randint(0, len(dataset) - 1)
        while pick in picks:
            pick = random.randint(0, len(dataset) - 1)
        picks.append(pick)

    df = pd.DataFrame(dataset[picks])
    print(df)


show_random_elements(librispeech["train"].remove_columns(["file"]), num_examples=20)



chars_to_ignore_regex = '[\,\?\.\!\-\;\:\"]'

def remove_special_characters(batch):
    batch["text"] = re.sub(chars_to_ignore_regex, '', batch["text"]).lower() + " "
    return batch

librispeech = librispeech.map(remove_special_characters)

show_random_elements(librispeech["train"].remove_columns(["file"]))


def extract_all_chars(batch):
  all_text = " ".join(batch["text"])
  vocab = list(set(all_text))
  return {"vocab": [vocab], "all_text": [all_text]}

vocabs = librispeech.map(extract_all_chars, batched=True, batch_size=-1, keep_in_memory=True, remove_columns=librispeech.column_names["train"])

vocab_list = list(set(vocabs["train"]["vocab"][0]) | set(vocabs["test"]["vocab"][0]))

vocab_dict = {v: k for k, v in enumerate(vocab_list)}
print(vocab_dict)

vocab_dict["|"] = vocab_dict[" "]
del vocab_dict[" "]
vocab_dict["[UNK]"] = len(vocab_dict)
vocab_dict["[PAD]"] = len(vocab_dict)
len(vocab_dict)


with open('../vocab.json', 'w') as vocab_file:
    json.dump(vocab_dict, vocab_file)


tokenizer = Wav2Vec2CTCTokenizer("../vocab.json", unk_token="[UNK]", pad_token="[PAD]", word_delimiter_token="|")

feature_extractor = Wav2Vec2FeatureExtractor(feature_size=1, sampling_rate=16000, padding_value=0.0, do_normalize=True, return_attention_mask=False)


processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)
processor.save_pretrained(PREPATH + "trained_model/")

print(librispeech["train"][0])


def speech_file_to_array_fn(batch):
    speech_array, sampling_rate = sf.read(batch["file"])
    batch["speech"] = speech_array
    batch["sampling_rate"] = sampling_rate
    batch["target_text"] = batch["text"]
    return batch

librispeech = librispeech.map(speech_file_to_array_fn, remove_columns=librispeech.column_names["train"], num_proc=4)


def prepare_dataset(batch):
    # check that all files have the correct sampling rate
    assert (
            len(set(batch["sampling_rate"])) == 1
    ), f"Make sure all inputs have the same sampling rate of {processor.feature_extractor.sampling_rate}."

    batch["input_values"] = processor(batch["speech"], sampling_rate=batch["sampling_rate"][0]).input_values

    with processor.as_target_processor():
        batch["labels"] = processor(batch["target_text"]).input_ids
    return batch

librispeech_prepared = librispeech.map(prepare_dataset, remove_columns=librispeech.column_names["train"], batch_size=8, num_proc=4, batched=True)

data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)
wer_metric = load_metric("wer")

def compute_metrics(pred):
    pred_logits = pred.predictions
    pred_ids = np.argmax(pred_logits, axis=-1)

    pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

    pred_str = processor.batch_decode(pred_ids)
    # we do not want to group tokens when computing the metrics
    label_str = processor.batch_decode(pred.label_ids, group_tokens=False)

    wer = wer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer}


model = Wav2Vec2ForCTC.from_pretrained(
    "facebook/wav2vec2-base",
    cache_dir=PREPATH + '/pretrained_model',
    gradient_checkpointing=True,
    ctc_loss_reduction="mean",
    pad_token_id=processor.tokenizer.pad_token_id,
)

model.freeze_feature_extractor()


training_args = TrainingArguments(
  output_dir=PREPATH + "./pretrained_model",
  group_by_length=True,
  per_device_train_batch_size=32,
  evaluation_strategy="steps",
  num_train_epochs=30,
  fp16=True,
  save_steps=500,
  eval_steps=500,
  logging_steps=500,
  learning_rate=1e-4,
  weight_decay=0.005,
  warmup_steps=1000,
  save_total_limit=2,
)

trainer = Trainer(
    model=model,
    data_collator=data_collator,
    args=training_args,
    compute_metrics=compute_metrics,
    train_dataset=librispeech_prepared["train"],
    eval_dataset=librispeech_prepared["test"],
    tokenizer=processor.feature_extractor,
)

trainer.train()

sys.stdout = open(PREPATH + "/console_output.txt", 'w')
sys.stdout.close()