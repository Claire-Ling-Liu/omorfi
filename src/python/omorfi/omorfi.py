#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Simple python interface for omorfi using libhfst-python. Consider this
class as a standard python interface to omorfi and standard reference for
scientific studies, as far as python use goes. For other interfaces, see
the standard shell scripts or java interface.
"""


from argparse import ArgumentParser
from glob import glob
from os import F_OK, access, getenv
from sys import stderr, stdin

import libhfst

from .settings import fin_punct_leading, fin_punct_trailing

can_udpipe = True
try:
    from ufal.udpipe import Model, Pipeline, ProcessingError
except ImportError:
    can_udpipe = False


class Omorfi:

    """
    An object holding omorfi binariesfor all the functions of omorfi.

    The following functionalities use automata binaries that need to be loaded
    separately:
    * analysis
    * tokenisation
    * generation
    * lemmatisation
    * segmentation
    * lookup
    * guess

    There is python code to perform basic string munging controlled by following
    bool attributes:
        try_lowercase: to use `str.lower()`
        try_titlecase: to use `str[0].upper() + str[1:]`
        try_uppercase: to use `str.upper()`
        try_detitlecase: to use `str[0].lower + str[1:]`

    The annotations will be changed when transformation has been applied.
    """
    analyser = None
    tokeniser = None
    generator = None
    lemmatiser = None
    hyphenator = None
    segmenter = None
    labelsegmenter = None
    acceptor = None
    guesser = None
    udpiper = None
    udpipeline = None
    uderror = None
    try_lowercase = True
    try_titlecase = True
    try_detitlecase = True
    try_uppercase = False
    can_analyse = False
    can_tokenise = True
    can_generate = False
    can_lemmatise = False
    can_hyphenate = False
    can_segment = False
    can_labelsegment = False
    can_guess = False
    can_udpipe = False

    _verbosity = False

    _stdpaths = ['/usr/local/share/hfst/fi/',
                 '/usr/share/hfst/fi/',
                 '/usr/local/share/omorfi/',
                 '/usr/share/omorfi/',
                 './', 'generated/', 'src/generated/', '../src/generated/']

    def __init__(self, verbosity=False):
        """Construct Omorfi with given verbosity for printouts."""
        self._verbosity = verbosity

    def load_filename(self, path, **include):
        """Load omorfi automaton from filename and guess its use.

        A file name should consist of three parts separated by full stop.
        The second part must be a keyword describing the use of the
        automaton, first part is parsed as an identifier typically starting
        with the word omorfi, followed by any extras, such as the tagset for
        analysis or generation.

        The named arguments can include a name of automaton type as name,
        and truth value as value, for types of automata allowed to load.
        By default, the names `analyse`, `generate` and `segment` are loaded.
        Names not included are defaulted to False. E.g.,
        `omorfi.load_filename(fn, analyse=True)`
        will only load file named fn if it can be identified as omorfi
        analyser. This is best used in conjunction with omorfi.load_from_dir.
        """
        if len(include) == 0:
            include['analyse'] = True
            include['generate'] = True
            include['segment'] = True
            include['accept'] = True
        for ttype in ['analyse', 'generate', 'accept', 'tokenise', 'lemmatise',
                      'hyphenate', 'segment', 'labelsegment', 'guesser',
                      'udpipe']:
            if ttype not in include:
                include[ttype] = False
        his = None
        if self._verbosity:
            print('Opening file', path)
        if access(path, F_OK):
            his = libhfst.HfstInputStream(path)
        else:
            # FIXME: should fail
            if self._verbosity:
                print('No access to ', path, file=stderr)
            pass
        parts = path[path.rfind('/') + 1:path.rfind('.')].split('.')
        if len(parts) != 2:
            if self._verbosity:
                print('not loaded', path)
        elif not parts[0] == 'omorfi':
            if self._verbosity:
                print('not omorfi', path)
        elif parts[1] == 'analyse' and include['analyse']:
            if self._verbosity:
                print('analyser', parts[0])
            self.analyser = his.read()
            self.can_analyse = True
            self.can_accept = True
            self.can_lemmatise = True
        elif parts[1] == 'generate' and include['generate']:
            if self._verbosity:
                print('generator', parts[0])
            self.generator = his.read()
            self.can_generate = True
        elif parts[1] == 'accept' and include['accept']:
            if self._verbosity:
                print('acceptor', parts[0])
            self.acceptor = his.read()
            self.can_accept = True
        elif parts[1] == 'tokenise' and include['tokenise']:
            if self._verbosity:
                print('tokeniser', parts[0])
            self.tokeniser = his.read()
            self.can_tokenise = True
        elif parts[1] == 'lemmatise' and include['lemmatise']:
            if self._verbosity:
                print('lemmatiser', parts[0])
            self.lemmatiser = his.read()
            self.can_lemmatise = True
        elif parts[1] == 'hyphenate' and include['hyphenate']:
            if self._verbosity:
                print('hyphenator', parts[0])
            self.hyphenator = his.read()
            self.can_hyphenate = True
        elif parts[1] == 'segment' and include['segment']:
            if self._verbosity:
                print('segmenter', parts[0])
            self.segmenter = his.read()
            self.can_segment = True
        elif parts[1] == 'guesser' and include['guesser']:
            if self._verbosity:
                print('guesser', parts[0])
            self.guesser = his.read()
            self.can_guess = True
        elif parts[1] == 'labelsegment' and include['labelsegment']:
            if self._verbosity:
                print('labelsegmenter', parts[0])
            self.labelsegmenter = his.read()
            self.can_segment = True
        elif self._verbosity:
            print('skipped', parts)

    def _maybe_str2token(self, s):
        if isinstance(s, str):
            return (s, "")
        else:
            return s

    def load_from_dir(self, path=None, **include):
        """Load omorfi automata from given or known locations.

        If path is given it should point to directory of automata,
        otherwise standard installation paths are tried. Currently standard
        linux install paths are all globbed in following order:

        * /usr/local/share/hfst/fi/*.hfst
        * /usr/share/hfst/fi/*.hfst
        * /usr/local/share/omorfi/*.hfst
        * /usr/share/omorfi/*.hfst
        * getenv('HOME') + /.hfst/fi/*.hfst
        * getenv('HOME') + /.omorfi/*.hfst

        Last two paths require getenv('HOME'). All automata matching
        glob *.hfst are loaded and stored in part of omorfi class appropriate
        for their usage.

        They keyword args can be used to limit loading of automata. The name
        is analyser type and value is True.
        """
        homepaths = []
        if getenv('HOME'):
            home = getenv('HOME')
            homepaths = [home + '/.hfst/fi/',
                         home + '/.omorfi/']
        loadable = []
        if path:
            if self._verbosity:
                print('adding', path + '/*.hfst')
            loadable = glob(path + '/*.hfst')
        else:
            for sp in self._stdpaths + homepaths:
                if self._verbosity:
                    print('adding', sp + '/*.hfst')
                loadable += glob(sp + '/*.hfst')
        for filename in loadable:
            try:
                self.load_filename(filename, **include)
            except:
                print("broken HFST", filename, file=stderr)

    def load_udpipe(self, filename):
        if not can_udpipe:
            print("importing udpipe failed, cannot load udpipe xxx")
            return
        self.udpiper = Model.load(filename)
        # use pipeline for now, ugly but workable
        self.udpipeline = Pipeline(self.udpiper, 'horizontal', Pipeline.DEFAULT,
                Pipeline.DEFAULT, 'conllu')
        self.uderror = ProcessingError()
        self.can_udpipe = True

    def _find_retoken_recase(self, token):
        if self.accept(token):
            return (token, "ORIGINALCASE")
        if self.try_lowercase and self.accept(token.lower()):
            return (token.lower(), "LOWERCASED=" + token)
        if self.try_uppercase and self.accept(token.upper()):
            return (token.upper(), "UPPERCASED=" + token)
        if len(token) > 1:
            if self.try_titlecase and self.accept(token[0].upper() + token[1:]):
                return (token[0].upper() + token[1:], "TITLECASED=" + token)
            if self.try_detitlecase and self.accept(token[0].lower() + token[1:]):
                return (token[0].lower() + token[1:], "DETITLECASED=" + token)
        return False

    def _find_retokens(self, token):
        retoken = self._find_retoken_recase(token)
        if retoken:
            return [retoken]
        # Word.
        if token[-1] in fin_punct_trailing:
            retoken = self._find_retoken_recase(token[:-1])
            if retoken:
                return[(retoken[0], retoken[1] + "|SpaceAfter=No"),
                       (token[-1], "SpaceBefore=No")]
        # -Word
        if token[0] in fin_punct_leading:
            retoken = self._find_retoken_recase(token[1:])
            if retoken:
                return [(token[0], "SpaceAfter=No"),
                        (retoken[0], retoken[1] + "|SpaceBefore=No")]
        # "Word"
        if token[0] in fin_punct_leading and token[-1] in fin_punct_trailing:
            retoken = self._find_retoken_recase(token[1:-1])
            if retoken:
                return [
                    (token[0], "SpaceAfter=No"),
                    (retoken[0], retoken[1] + "|SpaceBefore=No|SpaceAfter=No"),
                    (token[-1], "SpaceBefore=No")]
        # word." or word",
        if len(token) > 2 and token[-1] in fin_punct_trailing and token[-2] in fin_punct_trailing:
            retoken = self._find_retoken_recase(token[:-2])
            if retoken:
                return [
                    (retoken[0], retoken[1] + "|SpaceAfter=No"),
                    (token[-2], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-1], "SpaceBefore=No")]
        # word.",
        if len(token) > 3 and token[-1] in fin_punct_trailing and token[-2] in fin_punct_trailing and token[-3] in fin_punct_trailing:
            retoken = self._find_retoken_recase(token[:-3])
            if retoken:
                return [
                    (retoken[0], retoken[1] + "|SpaceAfter=No"),
                    (token[-3], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-2], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-1], "SpaceBefore=No")]
        # "word."
        if len(token) > 3 and token[-1] in fin_punct_trailing and token[-2] in fin_punct_trailing and token[0] in fin_punct_leading:
            retoken = self._find_retoken_recase(token[1:-2])
            if retoken:
                return [
                    (token[0], "SpaceAfter=No"),
                    (retoken[0], retoken[1] + "|SpaceBefore=No|SpaceAfter=No"),
                    (token[-2], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-1], "SpaceBefore=No")]
        # "word.",
        if len(token) > 4 and token[-1] in fin_punct_trailing and token[-2] in fin_punct_trailing and token[-3] in fin_punct_trailing and token[0] in fin_punct_leading:
            retoken = self._find_retoken_recase(token[1:-3])
            if retoken:
                return [
                    (token[0], "SpaceAfter=No"),
                    (retoken[0], retoken[1] + "|SpaceBefore=No|SpaceAfter=No"),
                    (token[-3], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-2], "SpaceBefore=No|SpaceAfter=No"),
                    (token[-1], "SpaceBefore=No")]
        # ...non-word...
        pretokens = []
        posttokens = []
        while len(token) > 1 and token[-1] in fin_punct_trailing:
            posttokens += [(token[-1], "SpaceBefore=No")]
            token = token[:-1]
        while len(token) > 1 and token[0] in fin_punct_leading:
            pretokens += [(token[0], "SpaceAfter=No")]
            token = token[1:]
        return pretokens + \
            [(token, "SpaceBefore=No|SpaceAfter=No")] + \
            posttokens

    def _retokenise(self, tokens):
        retokens = []
        for token in tokens:
            for retoken in self._find_retokens(token):
                retokens.append(retoken)
        return retokens

    def _tokenise(self, line):
        return None

    def tokenise(self, line):
        """Perform tokenisation with loaded tokeniser if any, or `split()`.

        If tokeniser is available, it is applied to input line and if
        result is achieved, it is split to tokens according to tokenisation
        strategy and returned as a list.

        If no tokeniser are present, or none give results, the line will be
        tokenised using python's basic string functions. If analyser is
        present, tokeniser will try harder to get some analyses for each
        token using hard-coded list of extra splits.
        """
        tokens = None
        if self.tokeniser:
            tokens = self._tokenise(line)
        if not tokens:
            tokens = self._retokenise(line.split())
        return tokens

    def _analyse_str(self, s):
        token = (s, "")
        res = self._analyse_token(token)
        if len(s) > 2 and s[0].islower() and self.try_titlecase:
            tcs = s[0].upper() + s[1:]
            if s != tcs:
                tctoken = (tcs, 'TitleCased=' + s)
                tcres = self._analyse_token(tctoken)
                for r in tcres:
                    r = (r[0] + '[CASECHANGE=TITLECASED]', r[1])
                res = res + tcres
        if len(token) > 2 and token[0].isupper() and self.try_detitlecase:
            dts = s[0].lower() + s[1:]
            if dts != s:
                dttoken = (dts, "DetitleCased=" + s)
                dtres = self._analyse_token(dttoken)
                for r in dtres:
                    r = (r[0] + '[CASECHANGE=DETITLECASED]', r[1])
                res = res + dtres
        if not s.isupper() and self.try_uppercase:
            ups = s.upper()
            if s != ups:
                uptoken = (ups, "UpperCased=" + s)
                upres = self._analyse_token(uptoken)
                for r in upres:
                    r = (r[0] + '[CASECHANGE=UPPERCASED]', r[1])
                res = res + upres
        if not s.islower() and self.try_lowercase:
            lows = s.lower()
            if s != lows:
                lowtoken = (lows, "LowerCased=" + s)
                lowres = self._analyse_token(lowtoken)
                for r in lowres:
                    r = (r[0] + '[CASECHANGE=LOWERCASED]', r[1])
                res += lowres
        return res

    def _analyse_token(self, token):
        res = self.analyser.lookup(token[0])
        for r in res:
            r = (r[0] + '[WEIGHT=%f]' % (r[1]), r[1], token[1])
        return res

    def analyse(self, token):
        """Perform a simple morphological analysis lookup.

        If try_titlecase does not evaluate to False,
        the analysis will also be performed with first letter
        uppercased and rest lowercased.
        If try_uppercase evaluates to not False,
        the analysis will also be performed on all uppercase variant.
        If try_lowercase evaluates to not False,
        the analysis will also be performed on all lowercase variant.

        The analyses with case mangling will have an additional element to them
        identifying the casing.
        """
        anals = None
        if isinstance(token, str):
            anals = self._analyse_str(token)
        else:
            anals = self._analyse_token(token)
        if not anals:
            if isinstance(token, str):
                anal = ('[WORD_ID=%s][GUESS=UNKNOWN][WEIGHT=inf]' %
                    (token), float('inf'), "Unknown")
            else:
                anal = ('[WORD_ID=%s][GUESS=UNKNOWN][WEIGHT=inf]' %
                    (token[0]), float('inf'), "Unknown")
            anals = [anal]
        return anals

    def analyse_sentence(self, s):
        """Analyse a full sentence with tokenisation and guessing.

        for details of tokenisation, see @c tokenise(self, s).
        for details of analysis, see @c analyse(self, token).
        If further models like udpipe are loaded, may fill in gaps with that.
        """
        tokens = self.tokenise(s)
        if not tokens:
            tokens = [(s, "ERRORS=analyse_sentence_1")]
        analyses = []
        for token in tokens:
            analyses += [self.analyse(token)]
        if self.can_udpipe:
            udinput = '\n'.join([token[0] for token in tokens])
            uds = self.udpipe(udinput)
        if len(uds) == len(analyses):
            for i in range(len(uds)):
                analsyses[i] += [uds[i]]
        return None

    def _guess_str(self, s):
        token = (s, "")
        return self._guess_token(token)

    def _guess_token(self, token):
        res = self.guesser.lookup(token[0])
        for r in res:
            r = (r[0] + '[GUESS=FSA][WEIGHT=%f]' % (r[1]), r[1], token[1])
        return res

    def _guess_heuristic(self, token):
        guess = (token[0], float('inf'), token[1])
        if token[0][0].isupper() and len(token[0]) > 1:
            guess = (token[0] + "[UPOS=PROPN][NUM=SG][CASE=NOM][GUESS=HEUR]" +
                     "[WEIGHT=28021984]", 28021984, token[1])
        else:
            guess = (token[0] + "[UPOS=NOUN][NUM=SG][CASE=NOM][GUESS=HEUR]" +
                     "[WEIGHT=28021984]", 28021984, token[1])
        return [guess]

    def guess(self, token):
        if not self.can_guess:
            if self.can_udpipe:
                return self._udpipe(token[0])
            else:
                return self._guess_heuristic(self._maybe_str2token(token))
        guesses = None
        if isinstance(token, str):
            guesses = self._guess_str(token)
        else:
            guesses = self._guess_token(token)
        return guesses

    def _lemmatise(self, token):
        res = self.lemmatiser.lookup(token)
        return res

    def lemmatise(self, token):
        lemmas = None
        lemmas = self._lemmatise(token)
        if not lemmas:
            lemma = (token, float('inf'))
            lemmas = [lemma]
        return lemmas

    def _segment(self, token):
        res = self.segmenter.lookup(token)
        return res

    def segment(self, token):
        segments = None
        segments = self._segment(token)
        if not segments:
            segment = (token, float('inf'))
            segments = [segment]
        return segments

    def _labelsegment(self, token):
        res = self.labelsegmenter.lookup(token)
        return res

    def labelsegment(self, token):
        labelsegments = None
        labelsegments = self._labelsegment(token)
        if not labelsegments:
            labelsegment = (token, float('inf'))
            labelsegments = [labelsegment]
        return labelsegments

    def _accept(self, token):
        res = self.acceptor.lookup(token)
        return res

    def accept(self, token):
        accept = False
        accepts = None
        accepts = self._accept(token)
        if accepts:
            accept = True
        return accept

    def _generate(self, omorstring):
        res = self.generator.lookup(omorstring)
        return res

    def generate(self, omorstring):
        generated = None
        if self.can_generate:
            generated = self._generate(omorstring)
            if not generated:
                generated = [(omorstring, float('inf'))]
        return generated

    def _udpipe(self, udinput):
        conllus = self.udpipeline.process(udinput, self.uderror)
        if self.uderror.occurred():
            return None
        tokens = []
        for conllu in conllus.split('\n'):
            if conllu.startswith('#'):
                continue
            elif conllu.strip() == '':
                continue
            tokens += [self._conllu2token(conllu)]
        return tokens

    def _conllu2token(self, conllu):
        fields = conllu.split()
        if len(fields) != 10:
            print("conllu2token conllu fail", fields)
        upos = fields[3]
        wordid = fields[2]
        surf = fields[1]
        ufeats = fields[5]
        misc = fields[9]
        analysis = '[WORD_ID=%s][UPOS=%s]%s[GUESS=UDPIPE]' %(wordid, upos,
                self._ufeats2omor(ufeats))
        return (analysis, float('inf'), misc)

    def _ufeats2omor(self, ufeats):
        return '[' + ufeats.replace('|', '][') + ']'

def main():
    """Invoke a simple CLI analyser."""
    a = ArgumentParser()
    a.add_argument('-f', '--fsa', metavar='FSAPATH',
                   help="Path to directory of HFST format automata")
    a.add_argument('-i', '--input', metavar="INFILE", type=open,
                   dest="infile", help="source of analysis data")
    a.add_argument('-v', '--verbose', action='store_true',
                   help="print verbosely while processing")
    options = a.parse_args()
    omorfi = Omorfi(options.verbose)
    if options.fsa:
        omorfi.load_from_dir(options.fsa)
    else:
        omorfi.load_from_dir()
    if not options.infile:
        options.infile = stdin
    if options.verbose:
        print("reading from", options.infile.name)
    for line in options.infile:
        line = line.strip()
        if not line or line == '':
            continue
        surfs = omorfi.tokenise(line)
        for surf in surfs:
            anals = omorfi.analyse(surf)
            print(surf, end='')
            for anal in anals:
                print("\t", anal[0], sep='', end='')
            print()
    exit(0)


if __name__ == "__main__":
    main()
