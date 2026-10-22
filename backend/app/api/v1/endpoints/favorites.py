import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.favorite import FavoriteFolder, FavoriteItem

router = APIRouter()


# --- Pydantic Request & Response Schemas ---

class CreateFolderRequest(BaseModel):
    name: str = Field(..., description="收藏夹名称")
    is_public: Optional[bool] = Field(False, description="是否公开，True为公开，False为私密")
    description: Optional[str] = Field(None, max_length=255, description="收藏夹简介")


class UpdateFolderRequest(BaseModel):
    name: Optional[str] = Field(None, description="收藏夹新名称")
    is_public: Optional[bool] = Field(None, description="是否公开")
    description: Optional[str] = Field(None, max_length=255, description="收藏夹简介")


class AddItemRequest(BaseModel):
    video_id: str = Field(..., description="短剧ID")
    folder_id: Optional[str] = Field(None, description="单收藏夹ID")
    folder_ids: Optional[List[str]] = Field(None, description="多收藏夹ID列表")


class QuickDefaultRequest(BaseModel):
    video_id: str = Field(..., description="短剧ID")


def serialize_folder(folder: FavoriteFolder, item_count: Optional[int] = None) -> Dict[str, Any]:
    count = item_count if item_count is not None else (len(folder.items) if folder.items else 0)
    return {
        "id": folder.id,
        "user_id": folder.user_id,
        "name": folder.name,
        "is_default": folder.is_default,
        "is_public": folder.is_public,
        "description": folder.description or "",
        "item_count": count,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
        "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
    }


def get_or_create_default_folder(db: Session, user: User) -> FavoriteFolder:
    """Ensure current user has at least one system default favorites folder."""
    folder = db.query(FavoriteFolder).filter(
        FavoriteFolder.user_id == user.id,
        FavoriteFolder.is_default == True
    ).first()
    if not folder:
        folder = FavoriteFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="默认收藏夹",
            is_default=True,
            is_public=False,
            description="默认收藏夹（私密）"
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
    return folder


# --- 1. GET /api/v1/favorites/folders ---
@router.get("/folders")
def list_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all favorite folders for current authenticated user.
    Auto-creates '默认收藏夹' if no folders exist.
    """
    # Ensure default folder exists
    get_or_create_default_folder(db, current_user)

    folders = db.query(FavoriteFolder).filter(
        FavoriteFolder.user_id == current_user.id
    ).order_by(desc(FavoriteFolder.is_default), desc(FavoriteFolder.created_at)).all()

    result = []
    for f in folders:
        cnt = db.query(FavoriteItem).filter(FavoriteItem.folder_id == f.id).count()
        result.append(serialize_folder(f, item_count=cnt))

    return result


# --- 2. POST /api/v1/favorites/folders ---
@router.post("/folders", status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: CreateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new custom named favorites folder.
    """
    name = payload.name.strip() if payload.name else ""
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="收藏夹名称不能为空"
        )

    # Check for name collision in current user's folders
    existing = db.query(FavoriteFolder).filter(
        FavoriteFolder.user_id == current_user.id,
        FavoriteFolder.name == name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"收藏夹 '{name}' 已存在，请使用其他名称"
        )

    folder = FavoriteFolder(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=name,
        is_default=False,
        is_public=bool(payload.is_public),
        description=payload.description.strip() if payload.description else None
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    return serialize_folder(folder, item_count=0)


# --- 3. PUT /api/v1/favorites/folders/{folder_id} ---
@router.put("/folders/{folder_id}")
def update_folder(
    folder_id: str,
    payload: UpdateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update favorites folder metadata (rename, change public/private visibility).
    Default folder cannot be renamed.
    """
    folder = db.query(FavoriteFolder).filter(
        FavoriteFolder.id == folder_id,
        FavoriteFolder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在或无权访问"
        )

    if payload.name is not None:
        clean_name = payload.name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="收藏夹名称不能为空"
            )
        if folder.is_default and clean_name != "默认收藏夹":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统默认收藏夹不可修改名称"
            )
        folder.name = clean_name

    if payload.is_public is not None:
        folder.is_public = payload.is_public

    if payload.description is not None:
        folder.description = payload.description.strip() if payload.description else None

    folder.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(folder)

    cnt = db.query(FavoriteItem).filter(FavoriteItem.folder_id == folder.id).count()
    return serialize_folder(folder, item_count=cnt)


# --- 4. DELETE /api/v1/favorites/folders/{folder_id} ---
@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete custom favorites folder and cascade delete contained items.
    Default folder is protected and cannot be deleted.
    """
    folder = db.query(FavoriteFolder).filter(
        FavoriteFolder.id == folder_id,
        FavoriteFolder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在或无权访问"
        )

    if folder.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统默认收藏夹受系统保护，不可删除"
        )

    db.delete(folder)
    db.commit()

    return {
        "success": True,
        "message": f"收藏夹 '{folder.name}' 及关联项目已成功删除",
        "deleted_folder_id": folder_id
    }


# --- 5. GET /api/v1/favorites/folders/{folder_id}/items ---
@router.get("/folders/{folder_id}/items")
def list_folder_items(
    folder_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    List items inside a folder with video details.
    Accessible if folder is public or belongs to authenticated user.
    """
    folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )

    if not folder.is_public:
        if not current_user or folder.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此私密收藏夹仅创建者可见"
            )

    items = db.query(FavoriteItem).filter(
        FavoriteItem.folder_id == folder.id
    ).order_by(desc(FavoriteItem.created_at)).all()

    results = []
    for it in items:
        vid = it.video
        first_ep = None
        if vid and vid.episodes and len(vid.episodes) > 0:
            first_ep = vid.episodes[0].id

        results.append({
            "id": it.id,
            "folder_id": it.folder_id,
            "video_id": it.video_id,
            "created_at": it.created_at.isoformat() if it.created_at else None,
            "video": {
                "id": vid.id if vid else it.video_id,
                "title": vid.title if vid else "未知短剧",
                "cover_url": (vid.cover_url or vid.custom_cover_url) if vid else None,
                "category": vid.category if vid else "短剧",
                "summary": vid.summary if vid else "",
                "total_episodes": vid.total_episodes if vid else 1,
                "author": vid.creator.nickname or vid.creator.username if (vid and vid.creator) else "官方精选",
                "duration": vid.episodes[0].duration_seconds if (vid and vid.episodes and len(vid.episodes) > 0) else 0,
                "first_episode_id": first_ep
            }
        })

    return results


# --- 6. POST /api/v1/favorites/items ---
@router.post("/favorites/items", status_code=status.HTTP_201_CREATED)
@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_favorite_item(
    payload: AddItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add drama to one or more user favorite folders.
    If no folder specified, saves to user's default folder.
    """
    video = db.query(Video).filter(Video.id == payload.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标短剧不存在"
        )

    # Determine target folder IDs
    target_ids = []
    if payload.folder_ids and len(payload.folder_ids) > 0:
        target_ids = payload.folder_ids
    elif payload.folder_id:
        target_ids = [payload.folder_id]
    else:
        def_folder = get_or_create_default_folder(db, current_user)
        target_ids = [def_folder.id]

    added_items = []
    for f_id in target_ids:
        folder = db.query(FavoriteFolder).filter(
            FavoriteFolder.id == f_id,
            FavoriteFolder.user_id == current_user.id
        ).first()
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"收藏夹 {f_id} 不存在或无权操作"
            )

        existing = db.query(FavoriteItem).filter(
            FavoriteItem.folder_id == f_id,
            FavoriteItem.video_id == video.id
        ).first()

        if not existing:
            item = FavoriteItem(
                id=str(uuid.uuid4()),
                folder_id=f_id,
                video_id=video.id,
                user_id=current_user.id
            )
            db.add(item)
            added_items.append(item)

    db.commit()
    for it in added_items:
        db.refresh(it)

    return {
        "success": True,
        "message": "已成功存入所选收藏夹",
        "video_id": video.id,
        "folder_ids": target_ids,
        "added_count": len(added_items)
    }


# --- Quick Default Toggle Helper ---
@router.post("/quick-default")
def quick_default_toggle(
    payload: QuickDefaultRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    1-click toggle to save or remove drama in user's default folder.
    """
    video = db.query(Video).filter(Video.id == payload.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标短剧不存在"
        )

    def_folder = get_or_create_default_folder(db, current_user)
    existing = db.query(FavoriteItem).filter(
        FavoriteItem.folder_id == def_folder.id,
        FavoriteItem.video_id == video.id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {
            "success": True,
            "is_favorited": False,
            "message": "已从默认收藏夹移出"
        }
    else:
        item = FavoriteItem(
            id=str(uuid.uuid4()),
            folder_id=def_folder.id,
            video_id=video.id,
            user_id=current_user.id
        )
        db.add(item)
        db.commit()
        return {
            "success": True,
            "is_favorited": True,
            "message": "已成功存入默认收藏夹"
        }


# --- 7. DELETE /api/v1/favorites/items/{id} ---
@router.delete("/items/{item_or_video_id}")
def remove_favorite_item(
    item_or_video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove item from favorites by item UUID or video ID across user's folders.
    """
    item = db.query(FavoriteItem).filter(
        FavoriteItem.id == item_or_video_id,
        FavoriteItem.user_id == current_user.id
    ).first()

    if item:
        db.delete(item)
        db.commit()
        return {"success": True, "message": "已从收藏夹移除", "deleted_item_id": item.id}

    # Fallback to delete by video_id
    items_by_video = db.query(FavoriteItem).filter(
        FavoriteItem.video_id == item_or_video_id,
        FavoriteItem.user_id == current_user.id
    ).all()

    if items_by_video:
        count = len(items_by_video)
        for it in items_by_video:
            db.delete(it)
        db.commit()
        return {"success": True, "message": f"已从 {count} 个收藏夹中移除该短剧", "deleted_count": count}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="未找到对应收藏项或无权移除"
    )


# Explicit folder-specific item deletion
@router.delete("/folders/{folder_id}/items/{video_id}")
def remove_item_from_folder(
    folder_id: str,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove video from a specific folder.
    """
    item = db.query(FavoriteItem).filter(
        FavoriteItem.folder_id == folder_id,
        FavoriteItem.video_id == video_id,
        FavoriteItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏项不存在于该收藏夹"
        )

    db.delete(item)
    db.commit()
    return {"success": True, "message": "已从收藏夹移除"}


# --- 8. GET /api/v1/favorites/status/{video_id} ---
@router.get("/status/{video_id}")
def check_favorite_status(
    video_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Check if current user has favorited a given video.
    Returns `is_favorited: bool` and list of `folder_ids`.
    """
    if not current_user:
        return {
            "is_favorited": False,
            "folder_ids": [],
            "item_ids": []
        }

    items = db.query(FavoriteItem).filter(
        FavoriteItem.user_id == current_user.id,
        FavoriteItem.video_id == video_id
    ).all()

    folder_ids = [it.folder_id for it in items]
    item_ids = [it.id for it in items]

    return {
        "is_favorited": len(items) > 0,
        "folder_ids": folder_ids,
        "item_ids": item_ids
    }
