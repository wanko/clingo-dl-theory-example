Set the library path to where `libclingo-dl.so` can be found:

    export LD_LIBRARY_PATH=<path-to-clingo-dl>/build/bin

The example emulates clingo-dl:

    python example.py -c n=132 example.lp --propagate full --stats 2
