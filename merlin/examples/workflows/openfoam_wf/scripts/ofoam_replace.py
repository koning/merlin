import argparse
import json
import os
import sys
from collections import OrderedDict



parser = argparse.ArgumentParser("Replace options in an OpenFoam input file")
parser.add_argument("-j", help="OpenFoam replacement variables in json encoded dict", default='{}')
parser.add_argument("-f", help="path to controlDict file", default="")

args = parser.parse_args()

filename = args.f

if not os.path.exists(filename):
    print("No controlDict file found: {0}".format(filename))
    sys.exit()

cDict = json.loads(args.j)

class OFfile():
    def __init__(self, filename):
        self.filename = filename
        self.read()

    def read(self):

        self.header = ""
        self.ff = ""
        self.opts = OrderedDict()
        self.seps = []
        ff = False
        of = False
        with open(self.filename) as f:
            for l in f:
                if "FoamFile" in l:
                    ff = True

                if (ff or of) and "//" in l:
                    self.seps.append(l)
                    if ff:
                       ff = False
                       of = True
                elif ff:
                    self.ff +=l
                elif of:
                    self.parse_opt(l)
                else:
                    self.header += l

    def show_values(self):
            print(self.header)
            print(30*'#')
            print(self.ff)
            print(30*'#')
            print("\n".join(["{0}\t{1};\n".format(k,v) for k,v in self.opts.items()]))
            print(30*'#')
            print(self.seps)

    def parse_opt(self, l):
        if not l:
            return

        ll = l.strip().split(" ")
        ll = list(filter(None, ll))
        if not ll:
            return

        if len(ll) > 1:
            ll[-1] = ll[-1].split(";")[0]
            self.opts[ll[0]] = " ".join(ll[1:])
        else:
            self.opts[ll[0]] = self.parse_dict(l)

    def parse_dict(self, l):
        return {}

    def replace(self, d):
        self.opts.update(d)

    def write(self):
        with open(self.filename,"w") as f:
            f.write(self.header)
            f.write(self.ff)
            f.write(self.seps[0]+"\n")
            f.write("\n".join(["{0: <15} {1};\n".format(k,v) for k,v in self.opts.items()]))
            f.write("\n"+self.seps[1])
        pass

if cDict:
    ofoamFile = OFfile(filename)
    ofoamFile.replace(cDict)
    ofoamFile.write()
