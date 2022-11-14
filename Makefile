
GVER="v4.6"

.PHONY: cldf
cldf:
	cldfbench makecldf --glottolog-version $(GVER) --with-cldfreadme --entry-point lexibank.dataset lexibank_pronouns.py
