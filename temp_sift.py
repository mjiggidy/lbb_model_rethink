import avb, sys

with avb.open(sys.argv[1]) as bin_handle:
	for sift_item in bin_handle.content.sifted_settings:
		print(sift_item.property_data)