"""저장 링크 API 테스트."""

import pytest
from fastapi.testclient import TestClient


def test_save_link(client: TestClient):
    """링크 저장."""
    # 폴더 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    # 링크 저장
    response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com/article",
            "display_title": "Example Article",
            "folder_id": folder_id,
            "note": "좋은 기사",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["display_title"] == "Example Article"
    assert data["note"] == "좋은 기사"
    assert data["member_folder_id"] == folder_id


def test_save_link_normalizes_url(client: TestClient):
    """URL 정규화 테스트."""
    # 폴더 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    # 첫 번째 링크 저장 (https로 정규화)
    response1 = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "http://example.com/article",  # http
            "display_title": "Article 1",
            "folder_id": folder_id,
        }
    )
    link_id_1 = response1.json()["link_id"]
    
    # 두 번째 링크 저장 (같은 URL, 다른 형식)
    response2 = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com/article",  # https
            "display_title": "Article 2",
            "folder_id": folder_id,
        }
    )
    link_id_2 = response2.json()["link_id"]
    
    # 같은 링크여야 함
    assert link_id_1 == link_id_2


def test_list_saved_links_by_folder(client: TestClient):
    """폴더별 저장 링크 조회."""
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
            "url": "https://example.com/1",
            "display_title": "Link 1",
            "folder_id": folder_id,
        }
    )
    client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com/2",
            "display_title": "Link 2",
            "folder_id": folder_id,
        }
    )
    
    # 조회
    response = client.get(f"/api/v1/members/1/folders/{folder_id}/saved_links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_saved_link(client: TestClient):
    """저장 링크 수정."""
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
            "display_title": "Original",
            "folder_id": folder_id,
        }
    )
    saved_link_id = save_response.json()["member_saved_link_id"]
    
    # 수정
    update_response = client.patch(
        f"/api/v1/members/1/saved_links/{saved_link_id}",
        json={
            "display_title": "Updated",
            "note": "수정됨",
        }
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_title"] == "Updated"


def test_delete_saved_link(client: TestClient):
    """저장 링크 삭제."""
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
            "display_title": "To Delete",
            "folder_id": folder_id,
        }
    )
    saved_link_id = save_response.json()["member_saved_link_id"]
    
    # 삭제
    delete_response = client.delete(f"/api/v1/members/1/saved_links/{saved_link_id}")
    assert delete_response.status_code == 204


def test_save_link_to_nonexistent_folder(client: TestClient):
    """존재하지 않는 폴더에 링크 저장."""
    response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com",
            "display_title": "Article",
            "folder_id": 999,
        }
    )
    assert response.status_code == 404
