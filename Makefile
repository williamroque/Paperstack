.PHONY: dist

dist:
	trash build dist
	python setup.py install
	python setup.py sdist
	twine upload dist/*
