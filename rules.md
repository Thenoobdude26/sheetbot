# Receipt extraction rules

## General
- Return only the fields below. If not clearly visible, return null. Never guess.

## Fields
- date: Payment date as YYYY-MM-DD. Two-digit years are 20xx.
  If both an invoice date and a billing period appear, use the invoice date.
- invoice_number: The invoice or receipt number, exactly as printed.
  If none, use the payment reference or booking code, else null.
- vendor: The company's common name, no Inc/Ltd. Known vendors, use exactly:
  Railway -> "Railway Corporation", Namecheap -> "Namecheap".
- description: One short line (under about 80 characters) saying what was bought,
  in the style of the sheet. Examples:
  "Domain Registration zykub.com"
  "Cloud Infrastructure (Disk, Memory, vCPU, Network, Hobby Plan)"
  Include the billing period if the receipt shows one.
  Never include card numbers, addresses or personal names.
  If you can't tell what was bought, use null.
- category: One of Hosting & Cloud, Domain & Hosting, Email, Other.
- amount: Final total paid including tax and fees, after discounts. Number only.
- currency: ISO code (USD, GBP, MYR). "RM" means MYR.


## Not a receipt
If the document is not a receipt or invoice, return null for every field.
