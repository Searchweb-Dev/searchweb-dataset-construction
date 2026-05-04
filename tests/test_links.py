"""링크 조회 API 테스트."""

import pytest
from fastapi.testclient import TestClient


def test_get_link(client: TestClient):
    """링크 조회."""
    # 폴더 및 링크 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    save_response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com",
            "display_title": "Example",
            "folder_id": folder_id,
        }
    )
    link_id = save_response.json()["link_id"]
    
    # 링크 조회
    response = client.get(f"/api/v1/links/{link_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["link_id"] == link_id
    assert data["canonical_url"] == "https://example.com"


def test_list_links_by_category(client: TestClient):
    """카테고리별 링크 조회."""
    # 폴더 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    # 링크 저장
    client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com",
            "display_title": "Article",
            "folder_id": folder_id,
        }
    )
    
    # 카테고리별 조회 (기본 카테고리 1)
    response = client.get("/api/v1/links?category_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_nonexistent_link(client: TestClient):
    """존재하지 않는 링크 조회."""
    response = client.get("/api/v1/links/999")
    assert response.status_code == 404
