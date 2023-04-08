##
# Lottery Data Scraper
#
# @file
# @version 0.1

FORCE:

test: FORCE
	python3 -m unittest discover tests

style: FORCE
	black .

# end
