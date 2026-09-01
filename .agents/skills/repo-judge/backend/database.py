import sqlite3
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

DB_PATH = Path(__file__).parent / "repo_judge.db"

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            project_name TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            result_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(result_dict: dict):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    analysis_id = result_dict["metadata"]["analysis_id"]
    timestamp = result_dict["metadata"]["timestamp"]
    project_name = result_dict["metadata"]["project_name"]
    overall_score = result_dict["semantic"]["report"]["overall"]["score"]
    
    cursor.execute('''
        INSERT INTO analyses (id, timestamp, project_name, overall_score, result_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (analysis_id, timestamp, project_name, overall_score, json.dumps(result_dict)))
    
    conn.commit()
    conn.close()

def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT result_json FROM analyses WHERE id = ?', (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None

def list_analyses() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT id, timestamp, project_name, overall_score FROM analyses ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "analysis_id": row[0],
            "timestamp": row[1],
            "project_name": row[2],
            "overall_score": row[3]
        }
        for row in rows
    ]

init_db()
