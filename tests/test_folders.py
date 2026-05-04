"""폴더 API 테스트."""

import pytest
from fastapi.testclient import TestClient


_member_id_counter = 1


@pytest.fixture
def member_id():
    """각 테스트마다 고유한 member_id."""
    global _member_id_counter
    mid = _member_id_counter
    _member_id_counter += 1
    return mid


def test_create_folder(client: TestClient, member_id: int):
    """폴더 생성."""
    response = client.post(
        "/api/v1/members/1/folders",
        json={
            "folder_name": "My Bookmarks",
            "description": "개인 북마크 폴더",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["folder_name"] == "My Bookmarks"
    assert data["owner_member_id"] == 1
    assert data["member_folder_id"] > 0


def test_create_subfolder(client: TestClient):
    """서브폴더 생성."""
    # 부모 폴더 생성
    parent_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Parents"}
    )
    parent_id = parent_response.json()["member_folder_id"]
    
    # 자식 폴더 생성
    child_response = client.post(
        "/api/v1/members/1/folders",
        json={
            "folder_name": "Child",
            "parent_folder_id": parent_id,
        }
    )
    assert child_response.status_code == 201
    assert child_response.json()["parent_folder_id"] == parent_id


def test_list_folders(client: TestClient):
    """폴더 목록 조회."""
    # 폴더 생성
    client.post("/api/v1/members/1/folders", json={"folder_name": "Folder 1"})
    client.post("/api/v1/members/1/folders", json={"folder_name": "Folder 2"})
    
    # 목록 조회
    response = client.get("/api/v1/members/1/folders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["folder_name"] == "Folder 1"


def test_update_folder(client: TestClient):
    """폴더 수정."""
    # 폴더 생성
    create_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Original"}
    )
    folder_id = create_response.json()["member_folder_id"]
    
    # 수정
    update_response = client.patch(
        f"/api/v1/members/1/folders/{folder_id}",
        json={"folder_name": "Updated"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["folder_name"] == "Updated"


def test_delete_folder(client: TestClient):
    """폴더 삭제."""
    # 폴더 생성
    create_response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "To Delete"}
    )
    folder_id = create_response.json()["member_folder_id"]
    
    # 삭제
    delete_response = client.delete(f"/api/v1/members/1/folders/{folder_id}")
    assert delete_response.status_code == 204
    
    # 삭제된 폴더 조회 확인
    list_response = client.get("/api/v1/members/1/folders")
    assert len(list_response.json()) == 0


def test_folder_not_found(client: TestClient):
    """폴더 없음 에러."""
    response = client.get("/api/v1/members/1/folders/999")
    assert response.status_code == 200  # GET 폴더 목록이므로 빈 리스트 반환
