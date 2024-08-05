#!/usr/bin/env python3

"""
Parses the CVE_PRODUCT (CPE) assignments in recipes (either all bitbake can
find, or the named set) and checks that the CPE is actually assigned.
"""

import collections
import dataclasses
import os
import pickle
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

@dataclasses.dataclass
class Product:
    cpe: str
    name: str = None
    homepage: str = None

# Map from CPE to Product
products = {}
# Map from homepage URL to list of CPEs
homepages = collections.defaultdict(list)

def normalise_url(url):
    """
    Normalise the URLs (specifically the path) so that github.com/foo/bar
    and github.com/foo/bar/ are the same.
    """

    # Path normalisation turns "" into ".", so bail early if empty
    if not url: return None

    parts = urllib.parse.urlparse(url)
    parts = parts._replace(path=os.path.normpath(parts.path))
    return urllib.parse.urlunparse(parts)


def parse_cpe_dictionary(filename):
    ns = {
        "dict": "http://cpe.mitre.org/dictionary/2.0"
    }

    root = ET.parse(filename)
    for item in root.iter("{http://cpe.mitre.org/dictionary/2.0}cpe-item"):
        cpe = item.get("name")
        cpe = urllib.parse.unquote(cpe.replace("cpe:/", ""))
        product_name = ":".join(cpe.split(":")[1:3])

        if product_name in products:
            product = products[product_name]
            continue
        else:
            product = Product(product_name)
            products[product_name] = product

        product.name = item.find("./dict:title", ns).text

        reference = item.find("./dict:references/dict:reference[.='Product']", ns)
        if reference is not None:
            product.homepage = normalise_url(reference.get("href"))

    return products

def bb(recipes=None):
    import bb.tinfoil

    with bb.tinfoil.Tinfoil() as tinfoil:
        tinfoil.prepare()

        pkg_pn = tinfoil.cooker.recipecaches[''].pkg_pn

        if not recipes:
            recipes = list(sorted(pkg_pn))

        for pn in recipes:
            for fn in pkg_pn[pn]:
                # TODO properly filter out class extension somehow
                if pn.startswith("nativesdk-") or pn.endswith("-native"):
                    continue

                realfn, _, _ = bb.cache.virtualfn2realfn(fn)
                data = tinfoil.parse_recipe_file(realfn)
                # TODO proper backslash unescaping
                cpes = (data.getVar("CVE_PRODUCT") or "").replace("\+", "+").split()

                print(f"{pn=}")
                for cpe in cpes:
                    if ":" in cpe:
                        # If the CPE is a vendor/product pair then we can check that
                        # it actually exists
                        if cpe in products:
                            print(f"Found {cpe}")
                        else:
                            print(f"Cannot find {cpe}")
                    else:
                        # If the CPE is just a product (typically ${BPN} as that is the default)
                        # then list all potential CPEs that match that product
                        matcher = fr".*:{re.escape(cpe)}$"
                        matches = [p for p in products if re.match(matcher, p)]
                        if matches:
                            print(f"Ambiguous CPE {cpe}, found {' '.join(matches)}")
                        else:
                            # If there are no matches based on the product, try looking for
                            # matching product homepages.
                            homepage = normalise_url(data.getVar("HOMEPAGE"))
                            if homepage and homepage in homepages:
                                matches = homepages[homepage]
                                print(f"Found from homepage: {' '.join(matches)}")
                            else:
                                print("Cannot find any matching CPE")


def pickle_save(filename, data):
    with open(filename, 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


def pickle_load(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    try:
        products = pickle_load("products.pickle")
    except FileNotFoundError:
        products = parse_cpe_dictionary("official-cpe-dictionary_v2.3.xml")
        pickle_save("products.pickle", products)

    for cpe, p in products.items():
        if p.homepage:
            homepages[p.homepage].append(cpe)

    bb(sys.argv[1:])
