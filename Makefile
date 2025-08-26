SHELL := /bin/bash

q ?= Pose ta question ici
model ?= qwen2.5:14b-instruct

.PHONY: pull-models coach sparring reviewer ask ingest

pull-models:
	ollama pull qwen2.5:14b-instruct || true
	ollama pull llama3.1:13b-instruct || true
	ollama pull qwen2.5:32b-instruct || true
	ollama pull llama3.1:70b-instruct || true

ingest:
	CHROMA_TELEMETRY_ENABLED=false ANONYMIZED_TELEMETRY=false CHROMA_ANONYMIZED_TELEMETRY=false
	python3 scripts/ingest.py

coach:
	CHROMA_TELEMETRY_ENABLED=false ANONYMIZED_TELEMETRY=false CHROMA_ANONYMIZED_TELEMETRY=false
	python3 scripts/run.py --preset coach --question "$(q)"

sparring:
	CHROMA_TELEMETRY_ENABLED=false ANONYMIZED_TELEMETRY=false CHROMA_ANONYMIZED_TELEMETRY=false
	python3 scripts/run.py --preset sparring --question "$(q)"

reviewer:
	CHROMA_TELEMETRY_ENABLED=false ANONYMIZED_TELEMETRY=false CHROMA_ANONYMIZED_TELEMETRY=false
	python3 scripts/run.py --preset reviewer --question "$(q)"

ask:
	CHROMA_TELEMETRY_ENABLED=false ANONYMIZED_TELEMETRY=false CHROMA_ANONYMIZED_TELEMETRY=false
	python3 scripts/run.py --model "$(model)" --question "$(q)"
	

