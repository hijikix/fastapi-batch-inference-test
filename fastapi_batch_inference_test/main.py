from contextlib import asynccontextmanager
import time
import asyncio
import queue

from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor


# バッチ処理する際の件数の閾値
BATCH_SIZE = 8

# メインのイベントループ（FastAPI起動時に設定）
MAIN_LOOP = None

batch_queue = queue.Queue()

# バッチループを回すexecutor
pool = ThreadPoolExecutor(max_workers=1)


async def dummy_inference(inputs: List[str]) -> List[str]:
    await asyncio.sleep(0.5)  # 推論処理の遅延をシミュレーション
    print(f"dummy_inference!!!: {inputs}")
    return [f"{item}-result" for item in inputs]


def pop_queue():
    print(f"batch_items size: {batch_queue.qsize()}")
    batch_items = []

    # 1つ目の要素が入るまで待機
    batch_items.append(batch_queue.get(block=True))

    # バッチサイズの最大値になるまでキューから取り出す
    for _ in range(BATCH_SIZE - 1):
        try:
            batch_items.append(batch_queue.get(block=False))
        except queue.Empty:
            # キューが空の場合抜ける
            pass

    return batch_items


def batch_processor():
    while True:
        batch_items = pop_queue()
        if not batch_items:
            continue

        # バッチ内の入力データを抽出
        inputs = [item["request_data"] for item in batch_items]

        # 推論処理を実行
        results = asyncio.run(dummy_inference(inputs))

        # 各リクエストに対して結果を返す
        for item, result in zip(batch_items, results):
            future = item["future"]
            # メインのイベントループに対して、Futureに結果を設定するように指示
            MAIN_LOOP.call_soon_threadsafe(future.set_result, result)


async def startup():
    """faseapiの起動時にバッチ処理のループを開始する"""
    print("startup")
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    MAIN_LOOP.run_in_executor(pool, batch_processor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield


app = FastAPI(lifespan=lifespan)


class PredictRequest(BaseModel):
    data: str


class PredictResponse(BaseModel):
    result: str


@app.post("/health")
def health():
    return {"Hello": "World"}


@app.post("/predict_one", response_model=PredictResponse)
async def predict_one(request: PredictRequest):
    results = await dummy_inference([request.data])
    return PredictResponse(result=results[0])


@app.post("/predict_batch", response_model=PredictResponse)
async def predict_batch(request: PredictRequest):
    future = asyncio.Future()
    batch_queue.put(
        {"request_data": request.data, "future": future, "timestamp": time.time()}
    )

    # バッチ推論の結果が返されるのを待つ
    result = await future
    return PredictResponse(result=result)
