from paddleocr import PaddleOCR
import time 

start_time = time.time()
ocr = PaddleOCR(lang="ch")
print(f"第二次初始化：{time.time() - start_time:.2f} sec")

start = time.time()
result = ocr.predict("python-mvp/tests/tmpE1CE.png")
print(f"推理时间: {time.time()-start:.2f}秒")