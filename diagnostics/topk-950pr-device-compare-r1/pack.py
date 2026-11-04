"""Use existing lossless B2Y transport for all three reports, without size assumptions."""
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
b2y = Path(__file__).resolve().parents[2]
path = b2y / "tools/b2y-result-parts/split_results.py"
spec = importlib.util.spec_from_file_location("result_transport", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sources = [(root.name + "-repeat-" + str(i) + ".json", root / ("repeat-" + str(i)) / "device-return.json") for i in (1, 2, 3)]
manifest = module.split_files(sources, b2y / "AAA_Results", prefix=root.name + "-parts")
print("UPLOAD_MANIFEST:", manifest)
for entry in json.loads(manifest.read_text())["files"]:
    for part in entry["parts"]:
        print("UPLOAD_PART:", manifest.parent / part["name"])
