from drive import upload_receipt

with open("test_receipts/pdf.pdf", "rb") as f:
    print(upload_receipt(f.read(), "test-upload.pdf", "application/pdf"))