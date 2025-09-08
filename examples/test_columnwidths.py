import sys
import avb
import pathlib

def get_bin_column_width_info(bin_content:avb.bin.Bin) -> str:

	import json
	return json.loads(bin_content.attributes.get("BIN_COLUMNS_WIDTHS").decode("utf-8"))

if __name__ == "__main__":

	if not len(sys.argv) > 1:	
		sys.exit(f"Usage: {__file__} bin_path.py")
	
	for bin_path in pathlib.Path(sys.argv[1]).rglob("*.avb", case_sensitive=False):

		if bin_path.name.startswith("."):
			continue
	
		with avb.open(bin_path) as bin_handle:
			try:
				binfo = get_bin_column_width_info(bin_handle.content)
				print(binfo, "\t", bin_path)
			except Exception as e:
				print(f"{bin_path}: {e}")