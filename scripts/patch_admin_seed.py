# -*- coding: utf-8 -*-
with open('backend/app/core/database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

seed_lines = [
    '                # 自动初始化管理员种子账号 (若 users 表为空，创建 admin / admin123)\n',
    '                try:\n',
    '                    from app.models.video import User\n',
    '                    from app.core.security import get_password_hash\n',
    '                    existing_admin = db.query(User).filter(User.username == "admin").first()\n',
    '                    if not existing_admin:\n',
    '                        seed_admin = User(\n',
    '                            username="admin",\n',
    '                            hashed_password=get_password_hash("admin123"),\n',
    '                            role="admin",\n',
    '                            nickname="系统管理员",\n',
    '                            is_active=True\n',
    '                        )\n',
    '                        db.add(seed_admin)\n',
    '                        db.commit()\n',
    '                        logger.info("Database seed: initial admin user (admin/admin123) seeded successfully.")\n',
    '                except Exception as user_seed_err:\n',
    '                    logger.warning(f"Initial admin seed notice: {user_seed_err}")\n'
]

# 插入到 line 147 之后 (即第 147 行是 logger.warning)
target_idx = -1
for i, l in enumerate(lines):
    if 'logger.warning(f"Agent fleet seed notice:' in l:
        target_idx = i + 1
        break

if target_idx != -1:
    lines[target_idx:target_idx] = seed_lines
    with open('backend/app/core/database.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)
    print("Patch success!")
else:
    print("Target index not found!")
