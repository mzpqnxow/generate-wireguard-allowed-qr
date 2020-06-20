all:
	@echo Installing qrcode Python module from pypi
	@python3 -mpip install -r requirements.txt

README.pdf: .FORCE
	pandoc  README.md -o README.pdf "-fmarkdown-implicit_figures -o" --from=markdown -V geometry:margin=.4in --toc --highlight-style=espresso

doc: README.md README.pdf

.PHONY : all doc .FORCE
