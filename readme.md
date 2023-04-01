# Portions of this code are Based on RWKV-v4neo from https://github.com/BlinkDL/RWKV-LM

# Python Server Environment

## Install Python Environment

Create an environment:

	conda env create -f environment.yml
	conda activate gpt

Updating

	conda env update --file environment.yml --prune

To delete an environment

	conda env remove -n gpt

## Install NextJS Environment

	cd packages/chat-client
	npm install

## Development

First begin by activating the conda environment and starting the python server:

	conda activate gpt
	cd ./server
	./start.sh

Next, in a new terminal tab, start the NEXTJS server

	cd packages/chat-client/
	npm run dev