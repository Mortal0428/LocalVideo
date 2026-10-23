import sys
sys.path.insert(0, "backend")
from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    print("Checking and migrating rag_eval_runs columns...")
    columns_to_add = [
        ("status", "VARCHAR(32) DEFAULT 'COMPLETED'"),
        ("progress", "INT DEFAULT 100"),
        ("current_step", "VARCHAR(255) DEFAULT '评测完成'"),
        ("logs_json", "LONGTEXT NULL")
    ]
    for col_name, col_type in columns_to_add:
        try:
            conn.execute(text(f"ALTER TABLE rag_eval_runs ADD COLUMN {col_name} {col_type}"))
            conn.commit()
            print(f"Added column {col_name} successfully.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Column {col_name} migration error: {e}")

    # 将原有记录的历史状态全部更新为 COMPLETED，进度 100%
    try:
        conn.execute(text("UPDATE rag_eval_runs SET status = 'COMPLETED', progress = 100 WHERE status IS NULL OR status = ''"))
        conn.commit()
        print("Updated legacy rows status to COMPLETED.")
    except Exception as e:
        print(f"Update error: {e}")

print("Migration finished!")
