.PHONY: press_clean_python
press_clean_python:
	-rm -rf $(shell find -L . -type d -name __pycache__)
