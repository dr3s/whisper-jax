import gradio as gr
import requests
from transformers.models.whisper.tokenization_whisper import TO_LANGUAGE_CODE


title = "Whisper JAX: The Fastest Whisper API Available ⚡️"

description = """Whisper JAX is an optimised implementation of the [Whisper model](https://huggingface.co/openai/whisper-large-v2) by OpenAI. It runs on JAX with a TPU v4-8 in the backend. Compared to PyTorch on an A100 GPU, it is over **12x** faster, making it the fastest Whisper API available.

You can submit requests to Whisper JAX through this Gradio Demo, or directly through API calls (see below). This notebook demonstrates how you can run the Whisper JAX model yourself on a TPU v2-8 in a Google Colab: TODO.
"""

API_URL = "https://whisper-jax.ngrok.io/generate/"

article = "Whisper large-v2 model by OpenAI. Backend running JAX on a TPU v4-8 through the generous support of the [TRC](https://sites.research.google/trc/about/) programme."

language_names = sorted(TO_LANGUAGE_CODE.keys())
SAMPLING_RATE = 16000


def query(payload):
    response = requests.post(API_URL, json=payload)
    return response.json(), response.status_code


def inference(inputs, task, return_timestamps):
    payload = {"inputs": inputs, "task": task, "return_timestamps": return_timestamps}

    data, status_code = query(payload)

    if status_code == 200:
        text = data["text"]
    else:
        text = data["detail"]

    if return_timestamps:
        timestamps = data["chunks"]
    else:
        timestamps = None

    return text, timestamps


def transcribe_audio(microphone, file_upload, task, return_timestamps):
    warn_output = ""
    if (microphone is not None) and (file_upload is not None):
        warn_output = (
            "WARNING: You've uploaded an audio file and used the microphone. "
            "The recorded file from the microphone will be used and the uploaded audio will be discarded.\n"
        )

    elif (microphone is None) and (file_upload is None):
        return "ERROR: You have to either use the microphone or upload an audio file"

    inputs = microphone if microphone is not None else file_upload

    inputs = {"array": inputs[1].tolist(), "sampling_rate": inputs[0]}

    text, timestamps = inference(inputs=inputs, task=task, return_timestamps=return_timestamps)

    return warn_output + text, timestamps


def _return_yt_html_embed(yt_url):
    video_id = yt_url.split("?v=")[-1]
    HTML_str = (
        f'<center> <iframe width="500" height="320" src="https://www.youtube.com/embed/{video_id}"> </iframe>'
        " </center>"
    )
    return HTML_str


def transcribe_youtube(yt_url, task, return_timestamps):
    html_embed_str = _return_yt_html_embed(yt_url)

    text, timestamps = inference(inputs=yt_url, task=task, return_timestamps=return_timestamps)

    return html_embed_str, text, timestamps


audio = gr.Interface(
    fn=transcribe_audio,
    inputs=[
        gr.inputs.Audio(source="microphone", optional=True),
        gr.inputs.Audio(source="upload", optional=True),
        gr.inputs.Radio(["transcribe", "translate"], label="Task", default="transcribe"),
        gr.inputs.Checkbox(default=False, label="Return timestamps"),
    ],
    outputs=[
        gr.outputs.Textbox(label="Transcription"),
        gr.outputs.Textbox(label="Timestamps"),
    ],
    allow_flagging="never",
    title=title,
    description=description,
    article=article,
)

youtube = gr.Interface(
    fn=transcribe_youtube,
    inputs=[
        gr.inputs.Textbox(lines=1, placeholder="Paste the URL to a YouTube video here", label="YouTube URL"),
        gr.inputs.Radio(["transcribe", "translate"], label="Task", default="transcribe"),
        gr.inputs.Checkbox(default=False, label="Return timestamps"),
    ],
    outputs=[
        gr.outputs.HTML(label="Video"),
        gr.outputs.Textbox(label="Transcription"),
        gr.outputs.Textbox(label="Timestamps"),
    ],
    allow_flagging="never",
    title=title,
    description=description,
    article=article,
)

demo = gr.Blocks()

with demo:
    gr.TabbedInterface([audio, youtube], ["Transcribe Audio", "Transcribe YouTube"])

demo.queue()
demo.launch()