"""태그 API 테스트."""

import pytest
from fastapi.testclient import TestClient


def test_create_tag(client: TestClient):
    """태그 생성."""
    response = client.post(
        "/api/v1/members/1/tags",
        json={"tag_name": "python-test1"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tag_name"] == "python-test1"
    assert data["owner_member_id"] == 1


def test_list_tags(client: TestClient):
    """태그 목록 조회."""
    client.post("/api/v1/members/1/tags", json={"tag_name": "python-test2"})
    client.post("/api/v1/members/1/tags", json={"tag_name": "javascript-test2"})
    
    response = client.get("/api/v1/members/1/tags")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_attach_tag_to_link(client: TestClient):
    """링크에 태그 부착."""
    # 폴더, 링크, 태그 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech-attach"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    save_response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com/attach",
            "display_title": "Article",
            "folder_id": folder_id,
        }
    )
    saved_link_id = save_response.json()["member_saved_link_id"]
    
    tag_response = client.post(
        "/api/v1/members/1/tags",
        json={"tag_name": "python-attach"}
    )
    tag_id = tag_response.json()["member_tag_id"]
    
    # 태그 부착
    attach_response = client.post(
        f"/api/v1/members/1/saved_links/{saved_link_id}/tags",
        json={"tag_id": tag_id}
    )
    assert attach_response.status_code == 201
    assert attach_response.json()["member_tag_id"] == tag_id


def test_detach_tag_from_link(client: TestClient):
    """링크에서 태그 제거."""
    # 폴더, 링크, 태그 생성
    folder_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech-detach"}
    )
    folder_id = folder_response.json()["member_folder_id"]
    
    save_response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com/detach",
            "display_title": "Article",
            "folder_id": folder_id,
        }
    )
    saved_link_id = save_response.json()["member_saved_link_id"]
    
    tag_response = client.post(
        "/api/v1/members/1/tags",
        json={"tag_name": "python-detach"}
    )
    tag_id = tag_response.json()["member_tag_id"]
    
    # 태그 부착
    client.post(
        f"/api/v1/members/1/saved_links/{saved_link_id}/tags",
        json={"tag_id": tag_id}
    )
    
    # 태그 제거
    detach_response = client.delete(
        f"/api/v1/members/1/saved_links/{saved_link_id}/tags/{tag_id}"
    )
    assert detach_response.status_code == 204


def test_attach_tag_to_nonexistent_link(client: TestClient):
    """존재하지 않는 링크에 태그 부착."""
    tag_response = client.post(
        "/api/v1/members/1/tags",
        json={"tag_name": "python-noexist"}
    )
    tag_id = tag_response.json()["member_tag_id"]
    
    response = client.post(
        "/api/v1/members/1/saved_links/999/tags",
        json={"tag_id": tag_id}
    )
    assert response.status_code == 404
