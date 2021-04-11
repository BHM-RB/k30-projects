import soundfile as sf
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# load pretrained model

tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-large-960h")

# load audio
audio_input, _ = sf.read("audio_example.flac")

# transcribe
input_values = tokenizer(audio_input, return_tensors="pt").input_values
logits = model(input_values).logits
predicted_ids = torch.argmax(logits, dim=-1)
transcription = tokenizer.batch_decode(predicted_ids)[0]
print(transcription)