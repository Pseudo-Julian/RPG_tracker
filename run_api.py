import uvicorn

if __name__ == "__main__":
    # host="0.0.0.0" / телефон в одній Wi-Fi мережі
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)