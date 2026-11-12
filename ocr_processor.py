import sys
import os
import logging

# 1. Force UTF-8 output to prevent Windows encoding exceptions in Java
sys.stdout.reconfigure(encoding='utf-8')

# 2. Quiet down C++ backend telemetry completely
os.environ["GLOG_minloglevel"] = "3"
logging.getLogger("ppocr").setLevel(logging.ERROR)

from paddleocr import PaddleOCR

if len(sys.argv) < 2:
    print("Error: Missing file path argument.")
    sys.exit(1)

image_path = sys.argv[1]

# 3. Initialize engine natively
ocr = PaddleOCR(lang='en')

# 4. Generate the 3.x prediction results array wrapper
result = ocr.predict(image_path)

# 5. Robust Extraction: Crawl whatever structure is returned to find 'rec_texts'
extracted_any_text = False

if result:
    for res in result:
        # Strategy A: Direct attribute or dictionary key access
        target_dict = None
        if hasattr(res, "res"):
            target_dict = res.res
        elif isinstance(res, dict) and "res" in res:
            target_dict = res["res"]
        else:
            target_dict = res

        # Extract text from target if it contains 'rec_texts'
        if target_dict and (isinstance(target_dict, dict) or hasattr(target_dict, "__getitem__")):
            try:
                if "rec_texts" in target_dict:
                    for text in target_dict["rec_texts"]:
                        print(str(text).strip())
                        extracted_any_text = True
            except Exception:
                pass

        # Strategy B: Hard fallback parsing by text pattern scanning if Strategy A fails
        if not extracted_any_text:
            raw_str = str(res)
            if "'rec_texts':" in raw_str:
                try:
                    # Cut out the array segment after rec_texts
                    parts = raw_str.split("'rec_texts':")[1].split("]")[0]
                    parts = parts.replace("[", "").replace("]", "")
                    for item in parts.split(","):
                        clean_item = item.strip().strip("'").strip('"')
                        if clean_item:
                            print(clean_item)
                            extracted_any_text = True
                except Exception:
                    pass

# Fallback C: If Paddle OCR falls back to standard line outputs
if not extracted_any_text and result:
    for page in result:
        if page:
            for line in page:
                if isinstance(line, list) and len(line) > 1 and isinstance(line[1], tuple):
                    print(line[1][0])
