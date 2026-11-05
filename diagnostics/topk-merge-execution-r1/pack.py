"""Losslessly split this single report using the established B2Y transport."""
import importlib.util
import json
from pathlib import Path
import sys
b2y=Path(__file__).resolve().parents[2]
path=b2y/"tools/b2y-result-parts/split_results.py"
spec=importlib.util.spec_from_file_location("merge_parts",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
source=Path(sys.argv[1]);manifest=module.split_files([(source.name,source)],b2y/"AAA_Results",prefix=source.stem+"-parts")
print("UPLOAD_MANIFEST",manifest)
for entry in json.loads(manifest.read_text())["files"]:
    for part in entry["parts"]:print("UPLOAD_PART",manifest.parent/part["name"])
