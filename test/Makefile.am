## Process this file with automake to produce Makefile.in

TESTS=rough-tests.sh scripts-runnable.sh \
	  tools-all-quick.bash \
	  faithfulness-ftb-3.1-quick.sh \
	  coverages-all-quick.sh \
	  faithfulness-ftb-3.1.sh \
	  conllu-fi-ud-test.sh \
	  conllu-fi-ftb-ud-test.sh
XFAIL_TESTS=
if WANT_BIG_TESTS
TESTS+=coverages-all-slow.bash
endif
if WANT_SMALL_LEXICONS
TESTS+=rougher-tests.bash coverages-less-quick.bash
XFAIL_TESTS+=rough-tests.sh coverages-all-quick.sh coverages-all-slow.bash
endif
EXTRA_DIST=rough-tests.sh \
		   scripts-runnable.sh \
		   wordforms.list \
		   wordforms-common.list \
		   coverage.py \
		   faithfulness.py \
		   conllu-compare.py

CLEANFILES=wordforms.anals

if CAN_YAML_TEST
#yaml-tests.yaml: test-header.yaml $(top_builddir)/src/lexical/gtd-tests.yaml
#	cat test-header.yaml gtd-tests.yaml > $@

endif


coverage-fast-alls.freqs: 5grams.uniq.freqs \
						  fiwiki-latest-pages-articles.uniq.freqs \
						  OpenSubtitles2016.fi.uniq.freqs \
						  ftb1-2014.uniq.freqs \
						  tatoeba-fi.uniq.freqs \
						  europarl-v7.fi-en.fi.uniq.freqs \
						  ftb3.1.uniq.freqs \
						  fi_ftb-ud.uniq.freqs \
						  gutenberg-fi.uniq.freqs \
						  vks.uniq.freqs \
						  fi-ud.uniq.freqs \
						  jrc-fi.uniq.freqs \
						  vns.uniq.freqs
	$(PYTHON) sum-uniq-freqs.py -o $@ -t 1000 $^

