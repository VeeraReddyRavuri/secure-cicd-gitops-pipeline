from fastapi import FastAPI, Response

app = FastAPI()


@app.get("/")
def read_root():
    return Response(content="failure", status_code=500)
