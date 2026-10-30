import os, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tmp = Path(tempfile.mkdtemp())
shutil.copytree(ROOT / "data" / "knowledge_base", tmp / "kb")   # tests never touch your real KB

os.environ["ANTHROPIC_API_KEY"] = ""          # tests always run offline
os.environ["KB_DIR"] = str(tmp / "kb")
os.environ["DB_PATH"] = str(tmp / "t.db")
sys.path.insert(0, str(ROOT))
