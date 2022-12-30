# export FLASK_APP=server
# flask run -h 0.0.0.0

from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import json
import os  
from os.path import exists
import time
import uuid



########################################################################################################
# The RWKV Language Model - https://github.com/BlinkDL/RWKV-LM
########################################################################################################

import numpy as np
import math, os, sys, types, time, gc
import torch
from src.utils import TOKENIZER

try:
    os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
except:
    pass
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cuda.matmul.allow_tf32 = True
np.set_printoptions(precision=4, suppress=True, linewidth=200)
args = types.SimpleNamespace()

########################################################################################################
# Step 1: set model & config
# Do this first: pip install torchdynamo
########################################################################################################

# args.RUN_DEVICE = "cuda"  # 'cpu' (already very fast) // 'cuda'
# args.FLOAT_MODE = "bf16" # fp32 (good for cpu) // fp16 (might overflow) // bf16 (less accurate)

args.RUN_DEVICE = "cpu"  # 'cpu' (already very fast) // 'cuda'
args.FLOAT_MODE = "fp32" # fp32 (good for cpu) // fp16 (might overflow) // bf16 (less accurate)

# if args.RUN_DEVICE == "cuda":
#     os.environ["RWKV_RUN_BACKEND"] = 'nvfuser' # !!!BUGGY!!! wrong output

TOKEN_MODE = "pile"
WORD_NAME = [
    "20B_tokenizer.json",
    "20B_tokenizer.json",
]  # [vocab, vocab] for Pile model
UNKNOWN_CHAR = None
vocab_size = 50277

# MODEL_NAME = '/Users/erik/RWKV-4-Pile-7B-20221115-8047'
# n_layer = 32
# n_embd = 4096
# ctx_len = 1024

MODEL_NAME = '/Users/erik/RWKV-4-Pile-1B5-20220929-ctx4096' # without the .pth
n_layer = 24
n_embd = 2048
ctx_len = 1024

args.MODEL_NAME = MODEL_NAME
args.n_layer = n_layer
args.n_embd = n_embd
args.ctx_len = ctx_len
args.vocab_size = vocab_size
args.head_qk = 0
args.pre_ffn = 0
args.grad_cp = 0
args.my_pos_emb = 0
os.environ["RWKV_RUN_DEVICE"] = args.RUN_DEVICE

NUM_TRIALS = 10 

TEMPERATURE = 1.0
top_p = 0.8
top_p_newline = 0.9  # only used in TOKEN_MODE = char

DEBUG_DEBUG = False  # True False --> show softmax output

########################################################################################################

print(f'\nUsing {args.RUN_DEVICE.upper()}. Loading {MODEL_NAME}...')
from src.model_run import RWKV_RNN

model = RWKV_RNN(args)

print(f'\nOptimizing speed...')
out, _ = model.forward([187], None)
# print(out)
gc.collect()
torch.cuda.empty_cache()

# input(0)

print(f'\nLoading tokenizer {WORD_NAME}...')
tokenizer = TOKENIZER(WORD_NAME, UNKNOWN_CHAR=UNKNOWN_CHAR)
if TOKEN_MODE == "pile":
    assert tokenizer.tokenizer.decode([187]) == '\n'

########################################################################################################

app = Flask(__name__)

@app.route('/api', methods=('GET', 'POST', 'OPTIONS'))
def api():
	if request.method == 'POST':
	
		request_json = request.get_json()
		
		prompt = request_json["prompt"]
		max_length = request_json["max_length"]
		stop = request_json["stop"]

		def generate(prompt, max_length, stop):
			print(prompt)

			context = prompt
		
			if tokenizer.charMode:
				context = tokenizer.refine_context(context)
				ctx = [tokenizer.stoi.get(s, tokenizer.UNKNOWN_CHAR) for s in context]
			else:
				ctx = tokenizer.tokenizer.encode(context)
			src_len = len(ctx)
			src_ctx = ctx.copy()

			print("\nYour prompt has " + str(src_len) + " tokens.")
			print(
				"Note: currently the first run takes a while if your prompt is long, as we are using RNN to preprocess the prompt. Use GPT to build the hidden state for better speed.\n"
			)

			time_slot = {}
			time_ref = time.time_ns()

			def record_time(name):
				if name not in time_slot:
					time_slot[name] = 1e20
				tt = (time.time_ns() - time_ref) / 1e9
				if tt < time_slot[name]:
					time_slot[name] = tt

			init_state = None
			init_out = None
			state = None
			out = None

			time_ref = time.time_ns()
			ctx = src_ctx.copy()

			for i in range(src_len):
				x = ctx[: i + 1]
				if i == src_len - 1:
					init_out, init_state = model.forward(x, init_state)
				else:
					init_state = model.forward(x, init_state, preprocess_only=True)
		
			gc.collect()
			torch.cuda.empty_cache()

			record_time('preprocess')
			out_last = src_len
			output = ''
		
			for i in range(src_len, src_len + (1 if DEBUG_DEBUG else max_length)):
				x = ctx[: i + 1]
				x = x[-ctx_len:]

				if i == src_len:
					out = init_out.clone()
					state = init_state.clone()
				else:
					out, state = model.forward(x, state)
				if DEBUG_DEBUG:
					print("model", np.array(x), "==>", np.array(out), np.max(out.cpu().numpy()), np.min(out.cpu().numpy()))
				if TOKEN_MODE == "pile":
					out[0] = -999999999  # disable <|endoftext|>

				ttt = tokenizer.sample_logits(
					out,
					x,
					ctx_len,
					temperature=TEMPERATURE,
					top_p_usual=top_p,
					top_p_newline=top_p_newline,
				)
				ctx += [ttt]

				if tokenizer.charMode:
					char = tokenizer.itos[ttt]
					print(char, end="", flush=True)
				else:
					char = tokenizer.tokenizer.decode(ctx[out_last:])
					if '\ufffd' not in char:
						print(char, end="", flush=True)
						out_last = i+1

				output += char

				if stop != None and str(output).endswith(stop):
					print("Halting due to STOP sequence")
					break
				
				yield json.dumps({
					"done": False,
					"prompt": str(prompt),
					"completion": str(output),
				}) + "\n"

			yield json.dumps({
				"done": True,
				"prompt": str(prompt),
				"completion": str(output),
			})

		response = Response(generate(prompt, max_length, stop))
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin,X-Requested-With,Content-Type,Accept,Authorization'
		return response

	def help_response():
		return 'POST here: {"prompt": "How do I walk a dog?", "max_length": 100, "stop": null}'

	response = Response(help_response())
	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Origin,X-Requested-With,Content-Type,Accept,Authorization'
	
	return response
