# Receipt extraction rules

## General
- Return only the fields listed below.
- If a field is not clearly visible, return null. Never guess.

## Fields
- date: The date the payment was made, as YYYY-MM-DD.
  If the year has two digits (e.g. "17 Oct 26"), assume 20xx.
  If there is both an invoice date and a billing period,
  use the invoice date.
- invoice_number: The invoice or receipt number printed on the
  document. If there is none, use the payment reference or booking
  code. If there is nothing like that either, null.
- vendor: The business that was paid, in plain form without
  suffixes ("Namecheap", not "Namecheap, Inc."). For delivery or
  ride apps, use the app's name (e.g. "Grab"), not the restaurant.
- category: Exactly one of the allowed categories below.
  If nothing fits, use "Other".
- amount: The final total actually paid, including tax and fees,
  after discounts. A number only, no currency symbol. Not the
  subtotal.
- currency: ISO code (USD, GBP, MYR). "RM" means MYR.

## Allowed categories
Hosting & Cloud, Domain & Hosting, Email, Software, Travel,
Food, Office, Other

## Not a receipt
If the document is not a receipt or invoice, return null for
every field.