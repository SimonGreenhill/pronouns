
GLOTTOLOG_VERSION="v4.7"

.PHONY: cldf
cldf:
	cldfbench makecldf --glottolog-version $(GLOTTOLOG_VERSION) --with-cldfreadme --entry-point lexibank.dataset lexibank_pronouns.py
