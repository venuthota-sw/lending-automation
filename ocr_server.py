from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
from PIL import Image
import anyio
import io
import logging
import numpy as np
import threading
import time

# Dedicated handler: PaddleX/uvicorn reconfigure the root logger at import,
# which can suppress INFO records. Own handler + propagate=False keeps our
# logs visible regardless.
log = logging.getLogger("ocr-server")
log.setLevel(logging.INFO)
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [ocr-server] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    log.addHandler(_handler)
log.propagate = False

app = FastAPI(title="OCR Server")

_ocr = None
_ocr_lock = threading.Lock()


def get_ocr():
    global _ocr
    if _ocr is None:
        device = "cpu"
        try:
            import paddle
            if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
                device = "gpu:0"
                log.info("CUDA GPU detected, PaddleOCR will use device=gpu:0")
        except Exception as e:
            log.warning("GPU detection failed, falling back to CPU: %s", e)
        _ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            device=device,
        )
        log.info("PaddleOCR initialized on device=%s", device)
    return _ocr


def _predict_sync(image_array):
    # PaddleOCR model instance is not thread-safe; serialize inference
    with _ocr_lock:
        return get_ocr().predict(image_array)


@app.post("/extract-text")
async def extract_text(request: Request, file: UploadFile = File(...)):
    start = time.perf_counter()
    filename = file.filename or "<unnamed>"
    request_id = request.headers.get("x-request-id", "-")
    try:
        image_bytes = await file.read()
        log.info("OCR request: id=%s file='%s', bytes=%d", request_id, filename, len(image_bytes))
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Offload blocking CPU inference so the event loop stays responsive
        result = await anyio.to_thread.run_sync(_predict_sync, np.array(image))
        texts = []
        for page in result:
            page_texts = page.get("rec_texts") or page.get("texts") or []
            texts.extend(page_texts)
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.info("OCR success: id=%s file='%s', elapsed=%.0f ms, lines=%d, chars=%d",
                 request_id, filename, elapsed_ms, len(texts), sum(len(t) for t in texts))
        return {"text": "\n".join(texts)}
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.error("OCR failed: id=%s file='%s', elapsed=%.0f ms, error=%s",
                  request_id, filename, elapsed_ms, e, exc_info=True)
        return JSONResponse(status_code=200, content={"error": str(e)})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    log.info("OCR server starting on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
