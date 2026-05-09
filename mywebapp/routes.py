from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
import mariadb

from mywebapp.models import ItemCreate
from mywebapp.db import get_db_connection

router = APIRouter()


def is_html_accepted(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept

@router.get("/", response_class=HTMLResponse)
def root_endpoints() -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Simple Inventory API</title></head>
    <body>
        <h1>API Endpoints (Simple Inventory)</h1>
        <ul>
            <li><a href="/items">GET /items</a> - Список усіх предметів</li>
            <li>POST /items - Створити новий запис</li>
            <li>GET /items/&lt;id&gt; - Детальна інформація</li>
            <li><a href="/health/alive">GET /health/alive</a> - Перевірка процесу</li>
            <li><a href="/health/ready">GET /health/ready</a> - Перевірка БД</li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/health/alive")
def health_alive() -> Response:
    return Response(content="OK", status_code=200, media_type="text/plain")


@router.get("/health/ready")
def health_ready(request: Request) -> Response:
    try:
        pool: mariadb.ConnectionPool = request.app.state.db_pool
        conn = pool.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return Response(content="OK", status_code=200, media_type="text/plain")
    except mariadb.Error as e:
        return Response(
            content=f"Database connection failed: {e}",
            status_code=500,
            media_type="text/plain"
        )


@router.get("/items")
def get_items(
    request: Request,
    conn: mariadb.Connection = Depends(get_db_connection)
) -> Response:
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name FROM items")
        rows: List[Dict[str, Any]] = cur.fetchall()
        cur.close()
    except mariadb.Error:
        raise HTTPException(status_code=500, detail="Database execution error")

    if is_html_accepted(request):
        rows_html = "".join([f"<tr><td>{row['id']}</td><td>{row['name']}</td></tr>" for row in rows])
        html = f"""
        <!DOCTYPE html><html><body>
        <h2>Inventory Items</h2>
        <table border='1'><tr><th>ID</th><th>Name</th></tr>{rows_html}</table>
        </body></html>
        """
        return HTMLResponse(content=html)
    
    return JSONResponse(content=rows)


@router.post("/items", status_code=201)
def create_item(
    item: ItemCreate,
    conn: mariadb.Connection = Depends(get_db_connection)
) -> JSONResponse:
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, quantity) VALUES (?, ?)",
            (item.name, item.quantity)
        )
        conn.commit()
        inserted_id = cur.lastrowid
        cur.close()
        return JSONResponse(
            content={"message": "Item created successfully", "id": inserted_id},
            status_code=201
        )
    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    request: Request,
    conn: mariadb.Connection = Depends(get_db_connection)
) -> Response:
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, name, quantity, created_at FROM items WHERE id = ?",
            (item_id,)
        )
        row: Dict[str, Any] | None = cur.fetchone()
        cur.close()
    except mariadb.Error:
        raise HTTPException(status_code=500, detail="Database execution error")
        
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    row['created_at'] = row['created_at'].isoformat()

    if is_html_accepted(request):
        html = f"""
        <!DOCTYPE html><html><body>
        <h2>Item Details: #{row['id']}</h2>
        <p><strong>Name:</strong> {row['name']}</p>
        <p><strong>Quantity:</strong> {row['quantity']}</p>
        <p><strong>Created At:</strong> {row['created_at']}</p>
        <a href="/items">Back to list</a>
        </body></html>
        """
        return HTMLResponse(content=html)
    
    return JSONResponse(content=row)