.PHONY: verify

verify:
	python3 -m unittest discover -s tests
	bash scripts/check-agent-ready.sh
	bash -n scripts/*.sh
	python3 scripts/validate-skills.py
	python3 scripts/validate-multica-config.py
	python3 scripts/validate-prompts.py
	python3 scripts/validate-workflows.py
	python3 scripts/validate-readme-paths.py
