.PHONY: docs

help:
	@echo "test - run the test py.test suite"
#	@echo "coverage - generate a coverage report and open it"
	@echo "docs - generate Sphinx HTML documentation and open it"
	@echo "apk - build an android apk with buildozer"
	@echo "deploy - deploy the app to your android device"
	@echo "clean - delete .buildozer folder for fresh build"

test:
	python setup.py test

# coverage:
#	 python setup.py test -a '--cov={{cookiecutter.repo_name}} --cov-report=html'
#	 xdg-open htmlcov/index.html

clean:
	buildozer appclean

docs:
	$(MAKE) -C docs html
	xdg-open docs/_build/html/index.html

apk:
	buildozer -v android debug

deploy:
	buildozer android debug deploy run; adb logcat | grep python &

run:
	./run_and_unlock.sh
