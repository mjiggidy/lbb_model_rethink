import sys
import avb
import itertools, pathlib

def get_bin_font_info(bin_content:avb.bin.Bin) -> str:

	return "\t".join([str(x) for x in [
		bin_content.attributes.get("ATTR__BIN_FONT_NAME"),
		bin_content.mac_font
	]])

if __name__ == "__main__":

	if not len(sys.argv) > 1:	
		sys.exit(f"Usage: {__file__} bin_path.py")
	
	for bin_path in pathlib.Path(sys.argv[1]).rglob("*.avb", case_sensitive=False):

		if bin_path.name.startswith("."):
			continue
	
		with avb.open(bin_path) as bin_handle:
			try:
				binfo = get_bin_font_info(bin_handle.content)
				print(binfo, "\t", bin_path)
			except Exception as e:
				print(f"{bin_path}: {e}")