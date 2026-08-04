from extract import extract_text
from explain import explain_topic

pdf_text = extract_text("sample.pdf")

print("PDF Loaded Successfully!\n")

print("Generating explanation...\n")

answer = explain_topic(pdf_text[:4000])

print(answer)